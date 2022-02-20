import csv

import numpy as np
import pandas as pd
from plumbum import cli
from preprocessor import Preprocessor


class FakeForecastCLI(cli.Application):
    preprocessor_parquet = cli.SwitchAttr("--preprocessor-parquet", str, mandatory=True)
    forecast_path = cli.SwitchAttr("--forecast-path", str, mandatory=True)
    sampling_type = cli.SwitchAttr(
        "--sampling-type", cli.switches.Set("proportional", "once", case_sensitive=False), mandatory=True
    )

    def main(self):
        preprocessor = Preprocessor(parquet_path=self.preprocessor_parquet)
        templates = preprocessor.get_grouped_dataframe_params().groupby("query_template").count()

        if self.sampling_type == "proportional":
            # Proportional sample of parameters, following the distribution of the counts.
            templates_with_param_vecs = [
                (template, preprocessor.sample_params(template, int(count)))
                for template, count in zip(templates.index.values, templates.values)
            ]
        else:
            assert self.sampling_type == "once"
            # Sample parameters once. Then use the same parameters for all queries in the query template.
            templates_with_param_vecs = [
                (template, np.tile(preprocessor.sample_params(template, 1)[0], (int(count), 1)))
                for template, count in zip(templates.index.values, templates.values)
            ]
        workload = [
            preprocessor.substitute_params(template, param_vec)
            for template, param_vecs in templates_with_param_vecs
            for param_vec in param_vecs
        ]
        workload = pd.DataFrame(workload, columns=["query"])
        predicted_queries = workload.groupby("query").size().sort_values(ascending=False)
        predicted_queries.to_csv(self.forecast_path, header=None, quoting=csv.QUOTE_ALL)


if __name__ == "__main__":
    FakeForecastCLI.run()
