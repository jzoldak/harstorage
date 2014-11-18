import math

class Aggregator():

    """
    Test results aggregation

    """

    def __init__(self, metrics=None):
        self.all_metrics = [
            {
                'id': "full_load_time",
                'title': "Full Load Time (ms)",
                'units': 'ms',
            },
            {
                'id': "requests",
                'title': "Total Requests",
                'units': 'count',
            },
            {
                'id': "total_size",
                'title': "Total Size (kB)",
                'units': 'kB',
            },
            {
                'id': "ps_scores",
                'title': "Page Speed Score",
                'units': 'count',
            },
            {
                'id': "onload_event",
                'title': "onLoad Event (ms)",
                'units': 'ms',
            },
            {
                'id': "start_render_time",
                'title': "Start Render Time (ms)",
                'units': 'ms',
            },
            {
                'id': "time_to_first_byte",
                'title': "Time to First Byte (ms)",
                'units': 'ms',
            },
            {
                'id': "total_dns_time",
                'title': "Total DNS Time (ms)",
                'units': 'ms',
            },
            {
                'id': "total_transfer_time",
                'title': "Total Transfer Time (ms)",
                'units': 'ms',
            },
            {
                'id': "total_server_time",
                'title': "Total Server Time (ms)",
                'units': 'ms',
            },
            {
                'id': "avg_connecting_time",
                'title': "Avg. Connecting Time (ms)",
                'units': 'ms',
            },
            {
                'id': "avg_blocking_time",
                'title': "Avg. Blocking Time (ms)",
                'units': 'ms',
            },
            {
                'id': "text_size",
                'title': "Text Size (kB)",
                'units': 'kB',
            },
            {
                'id': "media_size",
                'title': "Media Size (kB)",
                'units': 'kB',
            },
            {
                'id': "cache_size",
                'title': "Cache Size (kB)",
                'units': 'kB',
            },
            {
                'id': "redirects",
                'title': "Redirects",
                'units': 'count',
            },
            {
                'id': "bad_requests",
                'title': "Bad Rquests",
                'units': 'count',
            },
            {
                'id': "domains",
                'title': "Domains",
                'units': 'count',
            },
        ]

        self.METRICS = []
        for m in self.all_metrics:
            if metrics and m['id'] not in metrics:
                continue
            else:
                self.METRICS.append(m)

        self.data = self.data_container()

    def data_container(self):
        """Common data container"""

        data = dict()
        for metric in self.METRICS:
            data[metric['id']] = list()

        data["label"] = list()

        return data

    def add_row(self, label, row_index, documents):
        """Extract metrics from set of documents"""

        self.data["label"].append(row_index)
        self.data["label"][row_index] = label

        for metric in self.METRICS:
            self.data[metric['id']].append(row_index)
            self.data[metric['id']][row_index] = list()

        for document in documents:
            for metric in self.METRICS:
                if metric['id'] != "ps_scores":
                    self.data[metric['id']][row_index].append(
                        document[metric['id']]
                    )
                else:
                    self.data[metric['id']][row_index].append(
                        document[metric['id']]["Total Score"]
                    )

    def get_aggregated_value(self, list, agg_type, metric):
        """Return aggregated value in accordance with context(metric)"""

        if agg_type == "Average":
            return self.average(list)
        elif agg_type == "Minimum":
            return self.minimum(list)
        elif agg_type == "Maximum":
            return self.maximum(list)
        elif agg_type == "Median":
            return self.percentile(list, 0.5)
        elif agg_type == "90th Percentile":
            return self.percentile(list, 0.9)
        elif agg_type == "95th Percentile":
            return self.percentile(list, 0.95)
        elif agg_type == "99th Percentile":
            return self.percentile(list, 0.99)

    # def exclude_missing(self, points):
    #     """Remove points missing in all subsets"""

    #     index_oe = self.METRICS.index("onload_event")
    #     index_srt = self.METRICS.index("start_render_time")

    #     onload_event = points.split(";")[index_oe + 2]
    #     start_render_time = points.split(";")[index_srt + 2]

    #     number_of_values = onload_event.count("#") + 1
    #     broken_string = "#".join(["n/a"] * number_of_values)

    #     if onload_event == broken_string:
    #         points = points.replace("onLoad Event#", "")
    #     if start_render_time == broken_string:
    #         points = points.replace("Start Render Time#", "")

    #     return points.replace(broken_string + ";", "")

    def average(self, results):
        """
        @parameter results - a list of test results

        @return - the average value
        """

        try:
            num = len(results)
            total_sum = sum(results)
            return int(round(total_sum / num, 0))
        except TypeError:
            return "n/a"

    def minimum(self, results):
        """
        @parameter results - a list of test results

        @return - the minimum value
        """

        return min(results)

    def maximum(self, results):
        """
        @parameter results - a list of test results

        @return - the maximum value
        """

        return max(results)

    def percentile(self, results, percent, key=lambda x: x):
        """
        @parameter results - a list of test results
        @parameter percent - a float value from 0.0 to 1.0
        @parameter key - optional key function to compute value from each
        element of N.

        @return - the percentile
        """

        data = sorted(results)

        k = (len(data) - 1) * percent
        f = math.floor(k)
        c = math.ceil(k)

        if f == c:
            return key(data[int(k)])
        else:
            try:
                return key(data[int(f)]) * (c - k) + key(data[int(c)]) * (k - f)
            except TypeError:
                return "n/a"


class Histogram():

    """
    Statistical histograms based on Sturges rule

    """

    def __init__(self, data):
        """
        Initialize histogram parameters
        """

        self.data = sorted(data)
        self.size = len(self.data)
        self.max_value = max(self.data)
        self.min_value = min(self.data)

        if self.min_value != self.max_value:
            self.classes = round(1.0 + 3.32 * math.log10(self.size))
        else:
            self.classes = 1
        self.step = (self.max_value - self.min_value) / self.classes

    def ranges(self, reduced=False):
        ranges = list()

        for klass in range(int(self.classes)):
            range_l = int(self.min_value + self.step * klass)
            range_r = int(self.min_value + self.step * (klass + 1))

            if reduced:
                try:
                    order = 1 + int(100 / self.step)
                except:
                    order = 1

                range_l = round(range_l / 1000.0, order)
                range_r = round(range_r / 1000.0, order)

            ranges.append(str(range_l) + " - " + str(range_r))

        return ranges

    def frequencies(self):
        """
        Class (column) frequencies
        """

        frequencies = list()

        for index in range(int(self.classes)):
            frequencies.append(0)

        step = self.min_value + self.step

        index = 0

        for value in self.data:
            if value <= step:
                frequencies[index] += 1
            else:
                while value > step + 1:
                    step += self.step
                    index += 1
                try:
                    frequencies[index + 1] += 1
                except:
                    frequencies[index] += 1

        for index in range(int(self.classes)):
            frequencies[index] = round(frequencies[index] * 100.0 / self.size,
                                       1)

        return frequencies
