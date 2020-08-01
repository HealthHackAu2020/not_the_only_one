# #NotTheOnlyOne WebApp

## Notes

* Need to write your own config.py! See the sample config.py included

## Setup and running

Install conda (if needed):

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
```

Setup conda env and python modules:

```bash
conda create -n ntoo -c conda-forge python=3 redis mysqlclient pymysql
conda activate ntoo
pip install -r requirements.txt
```

Setup db with initial data:

```bash
python manage.py recreate_db && python manage.py setup
```

Run:

```bash
honcho start -e config.env -f Local
```
