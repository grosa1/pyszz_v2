# PySZZ v2
This is an open-source implementation of several versions of the SZZ algorithm for detecting bug-inducing commits.

## Requirements
To run PySZZ you need:

- Python 3
- srcML (https://www.srcml.org/) (i.e., the `srcml` command should be in the system path)
- git >= 2.23

## Setup
Run the following command to install the required python dependencies:
```
pip3 install --no-cache-dir -r requirements.txt
```

## Run
To run the tool, simply execute the following command:

```
python3 main.py /path/to/bug-fixes.json /path/to/configuration-file.yml /path/to/repo-directory
```
where:

- `bug-fixes.json` contains a list of information about bug-fixing commits and (optionally) issues <sup>[1](#myfootnote1)</sup>. 
This is an example json that can be used with pyszz:
```
[
  {
    "repo_name": "amirmikhak/3D-GIF",
    "fix_commit_hash": "645496dd3c5c89faee9dab9f44eb2dab1dffa3b9"
    "best_scenario_issue_date": "2015-04-23T07:41:52"
  },
  ...
]
```

alternatively:

```
[
  {
    "repo_name": "amirmikhak/3D-GIF",
    "fix_commit_hash":   "645496dd3c5c89faee9dab9f44eb2dab1dffa3b9",
    "earliest_issue_date": "2015-04-23T07:41:52"
  },
  ...
]
```

without issue date <sup>[1](#myfootnote1)</sup>:

```
[
  {
    "fix_commit_hash": "30ae3f5421bcda1bc4ef2f1b18db6a131dcbbfd3",
    "repo_name": "grosa1/szztest_mod_change"
  },
  ...
]
```

The issue date filter can be enabled using the param `issue_date_filter: true` in the config file. This filter removes all the commits when the `authored_date` is after the issue date reported as `earliest_issue_date` or `best_scenario_issue_date`. Note that if the issue date is reported without the timezone info, it is assumed to be `UTC`.

To avoid infinite loops during blame, a default timeout of `1 hour` is used. It can be manually modified at `szz.ma_szz.MASZZ.find_bic()#135`. This will impact on MA-SZZ, R-SZZ, L-SZZ, A-SZZ and DU-SZZ. 

- `configuration-file.yml` is one of the following, depending on the SZZ variant you want to run:
    - `conf/agszz.yaml`: runs AG-SZZ
    - `conf/lszz.yaml`: runs L-SZZ
    - `conf/rszz.yaml`: runs R-SZZ
    - `conf/maszz.yaml`: runs MA-SZZ
    - `conf/raszz.yaml`: runs RA-SZZ
    - `conf/pdszz.yaml`: runs PyDriller-SZZ
    - `conf/aszz.yaml`: runs A-SZZ@R
    - `conf/aszz_ma.yaml`: runs A-SZZ@MA
    - `conf/dfszz.yaml`: runs DU-SZZ@R
    - `conf/dfszz_ma.yaml`: runs DU-SZZ@MA
    - `conf/rszz+.yaml`: runs REV-SZZ@R
    - `conf/maszz+.yaml`: runs REV-SZZ@MA

Also, there are some variants of the default configuration files. For example, the conf files with the `_issues_filter` suffix run the corresponding SZZ variant with the issue filter enabled.

In each configuration file there is a comment for each param that explains its purpose. Note that for the param `file_ext_to_parse`, the file extension has to be lowercase because the filter calls `tolower()` on each file extension to check if there is a match.

- `repo-directory` is a folder which contains all the repositories that are required by `bug-fixes.json`. This parameter is not mandatory. In the case of the `repo-directory` is not specified, pyszz will download each repo required by each bug-fix commit in a temporary folder. In the other case, pyszz searches for each required repository in the `repo-directory` folder. The directory structure must be the following:

``` bash
    .
    |-- repo-directory
    |   |-- repouser
    |       |-- reponame 
    .
```

To have different run configurations, just create or edit the configuration files. The available parameters are described in each yml file. In order to use the issue date filter, you have to enable the parameter provided in each configuration file.

**N.B.** _the difference between `best_scenario_issue_date` and `earliest_issue_date` is described in our [paper](https://arxiv.org/abs/2102.03300). Simply, you can use `earliest_issue_date` if you have the date of the issue linked to the bug-fix commit._

**<a name="myfootnote1"><sup>1</sup></a>** You need to edit the flag `issue_date_filter` provided in the configuration files at `conf/` in order to enable/disable the issue date filter for SZZ.

## Quick start
- `start_example1.sh`, `start_example2.sh` and `start_example3.sh` are example usages of pyszz;
- `start_test_lszz.sh` and `start_test_rszz.sh` are test cases for L-SZZ and R-SZZ; 
-  The `test` directory contains some example resources, such as `repos_test.zip` and `repos_test_with_issues.zip`. They contain some downloaded repositories to be used with `bugfix_commits_test.json` and `bugfix_commits_with_issues_test.json` , which are two examples of input json containing bug-fixing commits;
- `postfilter_lszz.py` and `postfilter_rszz.py` can be used to apply only the heuristics of L-SZZ and R-SZZ to the output json of other SZZ (_e.g.,_ MA-SZZ) without performing a complete execution.

## How to cite
```
@article{rosa2023szzvariants,
  title     = {A comprehensive evaluation of SZZ Variants through a developer-informed oracle},
  author    = {Rosa, Giovanni and Pascarella, Luca and Scalabrino, Simone and Tufano, Rosalia and Bavota, Gabriele and Lanza, Michele and Oliveto, Rocco},
  journal   = {Journal of Systems and Software},
  volume    = {202},
  pages     = {111729},
  year      = {2023},
  publisher = {Elsevier}
  doi       = {10.1016/j.jss.2023.111729}
}
```

The replication package of the study is available [here](https://doi.org/10.6084/m9.figshare.19586500)
