#!/bin/bash

## PUT THIS INTO PYTHON SCRIPT TO USE MODULE
importers_base_path=""

#bioconductor
bioc_importer=$importers_base_path"/bioconductor/importer.py"
echo "Bioconductor importation starting ..."
python3 $bioc_importer
echo "Finished"

#biotools-bioconda
echo "OPEB biotools and bioconda importation stating ..."
biotools_bioconda_importer=$importers_base_path"/bioconda_biotools/importer.py"
#python3 $biotools_bioconda_importer
echo "Finished"

#galaxy
echo "Galaxy importation starting ..."
galaxy_importer=$importers_base_path"/galaxy/importer.py"
#python3 $galaxy_importer
echo "Finished"

#toolshed
echo "Galaxy Toolshed importation starting ..."
toolshed_importer=$importers_base_path"/toolshed/importer.py"
#python3 $toolshed_importer
echo "Finished"

#repositories
echo "Repos importation starting ..."
repositories_importer=$importers_base_path"/repositories/importer.py"
#python3 $repositories_importer
echo "Finished"

#metrics
echo "OPEB metrics starting ..."
metrics_importer=$importers_base_path"/opeb_metrics/importer.py"
#python3 $metrics_importer
echo "Finished"


