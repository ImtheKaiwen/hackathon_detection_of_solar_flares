from data_processor import DataProcessor
from sequence_generator import TimeSequenceGenerator

class CleanDataPipeline:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.sequence_generator = TimeSequenceGenerator()

    def step(self):
        self.data_processor.process_and_save()
        X_3d, df_hourly, harpnum_list = self.sequence_generator.generate()
        return X_3d, df_hourly, harpnum_list

if __name__ == '__main__':
    pipeline = CleanDataPipeline()
    pipeline.step()