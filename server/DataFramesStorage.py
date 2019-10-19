class DataFrames:
    '''
    {
    "device_name": <Name>,
    "datasets":
        [{
        "dataname":<Name>,
        "dataset":
            {
                'times' : [,]
                'values' : [,]
            }
        }]
    }
    '''
    def __init__(self, max_devices_count=1000, max_dataframes_count=1000):
        self.MaxDeviceCount = max_devices_count
        self.MaxDataframes = max_dataframes_count
        self.data_frames = {}

    def append(self, device_name, data_name, times, values):
        device = self.data_frames.get(device_name, None)
        if device is None:
            self.data_frames[device_name] = {}
            device = self.data_frames[device_name]
        data = device.get(data_name, None)
        if data is None:
            device[data_name] = {'times': [], 'values': []}
            data = device[data_name]

        if data is not None:
            (data['times']).extend(times)
            (data['values']).extend(values)

            frl = len(data['times'])
            if frl > self.MaxDataframes:
                count = frl - self.MaxDataframes
                data['times'] = data['times'][count:]
                data['values'] = data['values'][count:]

    @property
    def get(self):
        return self.data_frames

    @property
    def get_json(self):
        result = []
        for key in self.data_frames.keys():
            data_sets = []
            obj = {"device_name": key, "data_sets": data_sets}
            device = self.data_frames[key]
            for dk in device.keys():
                ds = device[dk]
                data_sets.append({"dataname": dk, "labels": ds['times'], 'series': ds['values']})
            result.append(obj)

        return result