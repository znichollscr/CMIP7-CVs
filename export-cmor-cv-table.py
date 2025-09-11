"""
Export CMOR CV table

To be moved somewhere more sensible
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pooch


def grab_from_universe(file_to_grab: str) -> dict[Any, Any]:
    """
    Grab data from the universe repo
    """
    commit_to_use = "e7c83a0e4232fbd87a4d8a5c877dda98702a31f0"

    known_hashes = {
        "WCRP-universe_frequency.json": "d96dcc2781ed9c088905cb282c7d0906e8feac22d447dc02900a3a2a0b1239be",
        "WCRP-universe_institution.json": "dafc1cf4b5841b169a84feb8f79b85d6f1f3d08cc3092fcb82f93dabad427005",
        "WCRP-universe_license.json": "43c9581df934b682ceabead92a3dd82ef28bf0859da4a5b574bf0ac16d6e1147",
        "WCRP-universe_resolution.json": "038eea7df2555f0d155ab0b9d35dfffed8183bd3a597bcabbc1db2f4f50acbc3",
        "WCRP-universe_realm.json": "4f14b51bf8b16a478f5c2cf030258596aaca1fc896cc621278133389d79d846d",
    }
    raw = pooch.retrieve(
        f"https://raw.githubusercontent.com/WCRP-CMIP/WCRP-universe/{commit_to_use}/{file_to_grab}",
        known_hash=known_hashes[file_to_grab] if file_to_grab in known_hashes else None,
    )

    with open(raw) as fh:
        res = json.load(fh)

    return res


def load_cmipld_style_str(cmipld_str: str) -> dict[Any, Any]:
    # TODO: use cmipld instead once I can get someone to explain it to me
    repo, path = cmipld_str.split(":")

    # TODO: make commits flexible
    if repo == "cmip7":
        repo_url = "https://raw.githubusercontent.com/WCRP-CMIP/CMIP7-CVs/4a5e9b6ab4738a479c2a5a7b23eb85f9ff94a243/src-data"

    elif repo == "universal":
        repo_url = "https://raw.githubusercontent.com/WCRP-CMIP/WCRP-universe/c8a435e51bf0f761b463f43c6f044d6c9fd55d75/src-data"

    else:
        raise NotImplementedError(repo)

    fp = pooch.retrieve(f"{repo_url}/{path}.json", known_hash=None)
    with open(fp) as fh:
        res = json.load(fh)

    return res


def main() -> None:
    OUT_FILE = "CMIP7-CV_for-cmor.json"
    REPO_ROOT = Path(__file__).parents[0]

    res = {
        "CV": {
            # TODO: Hard-coded, can we get these from elsewhere ?
            "archive_id": {
                "WCRP": "a collection of datasets from the AMIP and CMIP project phases, along with project supporting datasets from the input4MIPs (forcing datasets used to drive CMIP simulations) and obs4MIPs (observational datasets used to evaluate CMIP simulations, and numerous other supporting activities"
            },
            # TODO: Hard-coded, can we get these from elsewhere ?
            "branding_suffix": "<temporal_label><vertical_label><horizontal_label><area_label>",
            # TODO: Hard-coded, can we carry a version string round in the repo somewhere
            # (or will this global attribute be dropped?)
            "data_specs_version": "CMIP-7.0.0.0-alpha",
        }
    }

    # BUG: Need some actual info in here
    with open(REPO_ROOT / "CMIP7-CVs_drs.json") as fh:
        drs_info = json.load(fh)

    # TODO: get from esgvoc branch
    res["CV"]["DRS"] = drs_info["drs"]

    # TODO: get full area label set from somewhere, universe ?
    res["CV"]["area_label"] = {
        "air": "air",
        "lnd": "land",
        "u": 'unmasked (no "where" directive included in cell_methods)',
    }

    # TODO: check all entries and strip out anything we're not sure about
    with open(REPO_ROOT / "CMIP7-CVs_experiment.json") as fh:
        experiment_info = json.load(fh)

    res["CV"]["experiment_id"] = {}
    # for exp_export in experiment_info["experiment"]:
    for exp_export in ["historical", "piControl"]:
        eie = experiment_info["experiment"][exp_export]
        res["CV"]["experiment_id"][exp_export] = {}
        to_edit = res["CV"]["experiment_id"][exp_export]

        activity_info = load_cmipld_style_str(eie["activity"])
        # Again, don't love using validation-key rather than ID,
        # but ok we probably just have to document this
        to_edit["activity_id"] = [activity_info["validation-key"]]

        to_edit["additional_allowed_model_components"] = []
        to_edit["required_model_components"] = []
        for mr in eie["model-realms"]:
            mr_info = load_cmipld_style_str(mr["id"])
            if mr["is-required"]:
                key = "required_model_components"
            else:
                key = "additional_allowed_model_components"

            # Again, don't love using validation-key rather than ID,
            # but ok we probably just have to document this
            to_edit[key].append(mr_info["validation-key"])

        # TODO: check if fine to hard-code ?
        to_edit["host_collection"] = "CMIP7"

        if (
            eie["parent-experiment"] is None
            or eie["parent-experiment"] == "none"
            # TODO: double check values
            or eie["parent-experiment"].endswith("none")
        ):
            # TODO: double check values
            to_edit["parent_experiment_id"] = []
            to_edit["parent_activity_id"] = []

        else:
            parent_info = load_cmipld_style_str(eie["parent-experiment"])
            # Don't love this being validation-key rather than ID, but ok
            parent_activity_id = parent_info["activity"][0]
            if parent_activity_id == "cmip":
                parent_activity_id = "CMIP"

            to_edit["parent_experiment_id"] = [parent_info["validation-key"]]
            # TODO: double check values
            # (we're getting ID rather than the capitalised name,
            # probably need to retrieve through the CMIP-LD tree
            # to get the right thing)
            to_edit["parent_activity_id"] = [parent_activity_id]

        # BUG: start year vs. start date ?
        # CMOR uses "" for None rather than null
        to_edit["start_year"] = eie["start-date"] if eie["start-date"] else ""
        # BUG: end year vs. end date ?
        to_edit["end_year"] = eie["end-date"] if eie["end-date"] else ""

        to_edit["tier"] = eie["tier"]

        to_edit["description"] = eie["description"]
        # TODO: check if this is needed
        to_edit["experiment"] = eie["experiment"]
        # TODO: check if this mapping is correct
        to_edit["experiment_id"] = eie["validation-key"]
        to_edit["min_number_yrs_per_sim"] = eie["min_number_yrs_per_sim"]

    frequency_info = grab_from_universe("WCRP-universe_frequency.json")
    res["CV"]["frequency"] = {}
    for frequency, info in frequency_info["frequency"].items():
        res["CV"]["frequency"][frequency] = {
            # Is this meant to be in the universe? Or not needed?
            "approx_interval": None,
            "description": info["description"],
        }

    grid_label_info = grab_from_universe("WCRP-universe_grid-label.json")
    res["CV"]["grid_label"] = {}
    for grid_label, info in grid_label_info["grid-label"].items():
        res["CV"]["grid_label"][grid_label] = info["description"]

    # TODO: get full horizontal label set from somewhere, universe ?
    res["CV"]["horizontal_label"] = {
        "hm": "horizontal mean",
        "ht": "labeled areas",
        "hxy": "gridded",
        "hxys": "site values",
        "hy": "zonal mean",
        "hys": "basin mean",
    }

    # TODO: check registered insitutions and data content in universe
    institution_info = grab_from_universe("WCRP-universe_institution.json")
    res["CV"]["institution_id"] = {}
    for institution_id, info in institution_info["institution"].items():
        # ui-label doesn't feel like the right thing
        # but there's no full description
        res["CV"]["institution_id"][institution_id] = info["ui-label"]

    license_info = grab_from_universe("WCRP-universe_license.json")
    res["CV"]["license"] = {
        "license_id": {},
        "license_template": (
            "<license_id>; CMIP7 data produced by <institution_id> "
            "is licensed under a <license_type> License (<license_url>). "
            # TODO: check this link
            "Consult https://pcmdi.llnl.gov/CMIP7/TermsOfUse "
            "for terms of use governing CMIP7 output, "
            "including citation requirements and proper acknowledgment. "
            "The data producers and data providers make no warranty, "
            "either express or implied, including, but not limited to, "
            "warranties of merchantability and fitness for a particular purpose. "
            "All liabilities arising from the supply of the information "
            "(including any liability arising in negligence) "
            "are excluded to the fullest extent permitted by law."
        ),
    }
    for license_id, info in license_info["license"].items():
        # ui-label doesn't feel like the right thing
        # but there's no full description
        res["CV"]["license"]["license_id"][license_id] = {
            # ui-label feels like the wrong label, although information
            # seems to actually be the licence name
            "license_type": info["ui-label"],
            "license_url": info["url"],
        }

    # TODO: check fine to hard-code
    res["CV"]["mip_era"] = "CMIP7"

    nominal_resolution_info = grab_from_universe("WCRP-universe_resolution.json")
    res["CV"]["nominal_resolution"] = []
    for nominal_resolution in nominal_resolution_info["resolution"]:
        res["CV"]["nominal_resolution"].append(nominal_resolution)

    # TODO: check fine to hard-code
    res["CV"]["product"] = ["model-output"]

    realm_info = grab_from_universe("WCRP-universe_realm.json")
    res["CV"]["realm"] = {}
    for realm_id, info in realm_info["realm"].items():
        res["CV"]["realm"][realm_id] = info["description"]

    # TODO: get region label set from somewhere, universe ?
    # Not a thing with updated set up?
    res["CV"]["region"] = {
        "ant": "located around the South Pole, separated from other land masses by the Southern Ocean, and almost entirely south of 60 degrees South latitude",
        "glb": "the complete Earth surface, 90 degrees North to 90 degrees South latitude, and all longitudes",
        "gre": "located in the Northern Atlantic Ocean, separated from other land masses by the Labrador Sea and Straits, and almost entirely north of 60 degrees North latitude",
        "nhem": "the complete Earth surface from the equator to the North Pole, 0 to 90 degrees North latitude",
        "shem": "the complete Earth surface from the equator to the South Pole, 0 to 90 degrees South latitude",
    }

    # TODO: required global attributes missing from CVs - or should we get these from esgvoc ?
    res["CV"]["required_global_attributes"] = [
        "Conventions",
        "mip_era",
    ]

    # TODO: source ID missing from CVs - or should we be getting these from the universe
    # or building these from the information we already have?
    res["CV"]["source_id"] = {
        "PCMDI-test-1-0": {
            "activity_participation": ["CMIP"],
            "cohort": ["Registered"],
            "institution_id": ["PCMDI"],
            "label": "PCMDI-test 1.0",
            "label_extended": "PCMDI-test 1.0 (This entry is free text for users to contribute verbose information)",
            "model_component": {
                "aerosol": {"description": "none", "native_nominal_resolution": "none"},
                "atmos": {
                    "description": "Earth1.0-gettingHotter (360 x 180 longitude/latitude; 50 levels; top level 0.1 mb)",
                    "native_nominal_resolution": "1x1 degree",
                },
                "atmosChem": {
                    "description": "none",
                    "native_nominal_resolution": "none",
                },
                "land": {
                    "description": "Earth1.0",
                    "native_nominal_resolution": "1x1 degree",
                },
                "landIce": {"description": "none", "native_nominal_resolution": "none"},
                "ocean": {
                    "description": "BlueMarble1.0-warming (360 x 180 longitude/latitude; 50 levels; top grid cell 0-10 m)",
                    "native_nominal_resolution": "1x1 degree",
                },
                "ocnBgchem": {
                    "description": "none",
                    "native_nominal_resolution": "none",
                },
                "seaIce": {
                    "description": "Declining1.0-warming (360 x 180 longitude/latitude)",
                    "native_nominal_resolution": "1x1 degree",
                },
            },
            "release_year": "1989",
            "source": "PCMDI-test 1.0 (1989): \naerosol: none\natmos: Earth1.0-gettingHotter (360 x 180 longitude/latitude; 50 levels; top level 0.1 mb)\natmosChem: none\nland: Earth1.0\nlandIce: none\nocean: BlueMarble1.0-warming (360 x 180 longitude/latitude; 50 levels; top grid cell 0-10 m)\nocnBgchem: none\nseaIce: Declining1.0-warming (360 x 180 longitude/latitude)",
            "source_id": "PCMDI-test-1-0",
        }
    }

    source_type_info = grab_from_universe("WCRP-universe_source-type.json")
    res["CV"]["source_type"] = {}
    for source_type_id, info in source_type_info["source-type"].items():
        res["CV"]["source_type"][source_type_id] = info["description"]

    # TODO: get full temporal label set from somewhere, universe ?
    res["CV"]["temporal_label"] = {
        "tavg": "mean",
        "tclm": "climatology",
        "tclmdc": "diurnal cycle climatology",
        "ti": "time independent",
        "tpt": "point",
        "tstat": "statistic",
        "tsum": "sum",
    }

    # TODO: check fine to hard-code
    res["CV"]["tracking_id"] = ["hdl:21.14100/.*"]

    with open(REPO_ROOT / "CMIP7-CVs_index.json") as fh:
        index_info = json.load(fh)

    res["CV"]["variant_label"] = [index_info["index"]["variant-label"]]

    # TODO: get full vertical label set from somewhere, universe ?
    res["CV"]["vertical_label"] = {
        "1000hPa": "1000 hPa",
        "100hPa": "100 hPa",
        "10hPa": "10 hPa",
        "220hPa": "220 hPa",
        "500hPa": "500 hPa",
        "560hPa": "560 hPa",
        "700hPa": "700 hPa",
        "840hPa": "840 hPa",
        "850hPa": "850 hPa",
        "d0m": "surface",
        "d100m": "100m depth",
        "d10cm": "1cm depth",
        "d1m": "1m depth",
        "d2000m": "2000m depth",
        "d300m": "300m depth",
        "d700m": "700m depth",
        "h100m": "100m height",
        "h10m": "10m height",
        "h16": "16 height levels",
        "h2m": "2m height",
        "h40": "40 height levels",
        "l": "model level",
        "p19": "19 pressure levels",
        "p27": "27 pressure levels",
        "p3": "3 pressure levels",
        "p39": "39 pressure levels",
        "p4": "4 pressure levels",
        "p7c": "7 pressure levels",
        "p7h": "7 pressure levels",
        "p8": "8 pressure levels",
        "rho": "density surface",
        "u": "unspecified (no vertical dimension)",
    }

    with open(OUT_FILE, "w") as fh:
        json.dump(res, fh, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()
