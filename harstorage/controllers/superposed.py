from pylons import request, tmpl_context as c
from pylons import config
from pylons.decorators.rest import restrict

from harstorage.lib.base import BaseController, render
from harstorage.lib.MongoHandler import MongoDB
from harstorage.lib.math_helpers import Histogram, Aggregator


class SuperposedController(BaseController):

    """
    Interface for aggregation and comparison of test results

    """

    def  __init__(self, *args, **kwargs):
        super(SuperposedController, self).__init__(*args, **kwargs)
        
        # Aggregator
        metrics = request.GET.getall('metrics')
        self.agg_types = metrics if len(metrics) > 0 else None

        agg_types = request.GET.getall('agg_types')
        self.agg_types = agg_types if len(agg_types) > 0 else ['Average']

        self.aggregator = Aggregator(metrics=metrics)

        # Mongo handler
        self.md_handler = MongoDB()

    def __before__(self):
        """
        Define version of static content
        """
        c.rev = config["app_conf"]["static_version"]
    
    @restrict("GET")
    def get_docs(self, condition):
        # Read data from database
        fields =[m['id'] for m in self.aggregator.METRICS]
        return self.md_handler.collection.find(condition, fields=fields)

    @restrict("GET")
    def create(self):
        """
        Render form with list of labels and timestamps
        """

        if hasattr(c, "message"):
            return render("/error.html")

        # List of labels
        c.labels = list()

        for label in self.md_handler.collection.distinct("label"):
            c.labels.append(label)

        c.agg_types = [
            "Average",
            "Median",
            "Minimum",
            "90th Percentile",
            "95th Percentile",
            "99th Percentile",
            "Maximum",
        ]

        c.metrics = [m['id'] for m in Aggregator().all_metrics]

        return render("/create/core.html")

    @restrict("GET")
    def dates(self):
        """
        Return a list of timestamps for selected label
        """

        # Read label from GET request
        label = request.GET["label"]

        # Read data from database
        documents = MongoDB().collection.find(
            {"label": label},
            fields=["timestamp"],
            sort=[("timestamp", 1)])

        dates = str()
        for document in documents:
            dates += document["timestamp"] + ";"

        return dates[:-1]

    @restrict("GET")
    def display(self):
        """
        Render page with column chart and data table
        """

        if hasattr(c, "message"):
            return render("/error.html")

        # Checkbox options
        c.chart_type = request.GET.get("chart", None)
        c.table = request.GET.get("table", "false")
        c.chart = "true" if c.chart_type else "false"

        # Aggregation option
        c.agg_types = self.agg_types

        # Data table
        c.headers = ["Label"]
        c.metrics_table = list()
        c.metrics_table.append(list())

        # Chart points
        c.points = str()

        # Test results from database
        c.rowcount = len([key for key in request.GET.keys() if key.startswith('step_') and key.endswith('_label')])
        for row_index in range(c.rowcount):
            # Parameters from GET request
            label = request.GET["step_" + str(row_index + 1) + "_label"]
            start_ts = request.GET["step_" + str(row_index + 1) + "_start_ts"]
            end_ts = request.GET["step_" + str(row_index + 1) + "_end_ts"]

            # Add label
            c.metrics_table[0].append(label)
            c.points += label + "#"

            # Fetch test results
            condition = {
                "label": label,
                "timestamp": {"$gte": start_ts, "$lte": end_ts}
            }
            documents = self.get_docs(condition)

            # Add data row to aggregator
            self.aggregator.add_row(label, row_index, documents)

        # Aggregated data per column
        column = 1
        titles = str()
        for metric in sorted(self.aggregator.METRICS, key=lambda t: t['id'], reverse=True):
            for agg_type in c.agg_types:
                mod_title = metric['title'] + ' ({})'.format(agg_type)
                c.headers.append(mod_title)
                c.metrics_table.append(list())
                c.points = c.points[:-1] + ";"

                for row_index in range(c.rowcount):
                    data_list = self.aggregator.data[metric['id']][row_index]
                    value = self.aggregator.get_aggregated_value(data_list, agg_type,
                                                            metric['id'])

                    c.points += str(value) + "#"
                    c.metrics_table[column].append(value)

                column += 1
                titles += mod_title + "#"


        # Final chart points
        c.points = titles[:-1] + ";" + c.points[:-1]

        return render("/display/core.html")

    def histogram(self):
        """
        Render chart with histograms
        """

        if hasattr(c, "message"):
            return render("/error.html")

        # Options
        c.label = request.GET["label"]
        c.metric = request.GET["metric"]

        # Metrics
        metrics = self.aggregator.METRICS
        c.metrics = list()

        # Read data from database
        documents = self.get_docs({"label": c.label})
        full_data = list(document for document in documents)

        for metric in metrics:
            try:
                data = (result[metric['id']] for result in full_data)
                histogram = Histogram(data)

                if metric['unit'] == 'ms':
                    ranges = histogram.ranges(True)
                else:
                    ranges = histogram.ranges()

                frequencies = histogram.frequencies()

                if metric['id'] == c.metric:
                    c.data = ""

                    for occ_range in ranges:
                        c.data += occ_range + "#"

                    c.data = c.data[:-1] + ";"

                    for frequency in frequencies:
                        c.data += str(frequency) + "#"

                    c.data = c.data[:-1] + ";"

                    c.title = metric['title']

                c.metrics.append((metric['id'], metric['title']))
            except IndexError:
                pass
            except TypeError:
                pass
            except ValueError:
                pass

        if len(c.metrics):
            return render("/histogram/core.html")
        else:
            c.message = "Sorry! You haven't enough data."
            return render("/error.html")
