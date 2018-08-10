#!/usr/bin/python
import logging
import shutil

import argschema as ags

import allensdk.ipfx.data_set_features as dsft
from allensdk.ipfx.ephys_data_set import EphysDataSet, StimulusOntology
from allensdk.ipfx._schemas import FeatureExtractionParameters
from allensdk.ipfx.aibs_data_set import AibsDataSet

import allensdk.core.json_utilities as ju
from allensdk.core.nwb_data_set import NwbDataSet


def embed_spike_times(input_nwb_file, output_nwb_file, sweep_features):
    # embed spike times in NWB file
    logging.debug("Embedding spike times")
    tmp_nwb_file = output_nwb_file + ".tmp"

    shutil.copy(input_nwb_file, tmp_nwb_file)
    for sweep_num in sweep_features:
        spikes = sweep_features[sweep_num]['spikes']
        spike_times = [ s['threshold_t'] for s in spikes ]
        NwbDataSet(tmp_nwb_file).set_spike_times(sweep_num, spike_times)

    try:
        shutil.move(tmp_nwb_file, output_nwb_file)
    except OSError as e:
        logging.error("Problem renaming file: %s -> %s" % (tmp_nwb_file, output_nwb_file))
        raise e




def run_feature_extraction(input_nwb_file, stimulus_ontology_file, output_nwb_file, qc_fig_dir, sweep_info, cell_info):

    ont = StimulusOntology(ju.read(stimulus_ontology_file)) if stimulus_ontology_file else None
    data_set = AibsDataSet(sweep_info=sweep_info,
                           nwb_file=input_nwb_file,
                           ontology=ont,
                           api_sweeps=False)



    cell_features, sweep_features, cell_record, sweep_records = dsft.extract_data_set_features(data_set)

    if cell_info:
        cell_record.update(cell_info)

    feature_data = { 'cell_features': cell_features,
                     'sweep_features': sweep_features,
                     'cell_record': cell_record,
                     'sweep_records': sweep_records }

    embed_spike_times(input_nwb_file, output_nwb_file, sweep_features)
#    display_features(qc_fig_dir, data_set, feature_data, plot_sweep_figures=True, plot_cell_figures=False)

    return feature_data


def main():
    module = ags.ArgSchemaParser(schema_type=FeatureExtractionParameters)

    feature_data = run_feature_extraction(module.args["input_nwb_file"],
                                          module.args.get("stimulus_ontology_file", None),
                                          module.args["output_nwb_file"],
                                          module.args["qc_fig_dir"],
                                          module.args["sweep_props"],
                                          module.args["cell_features"])

    ju.write(module.args["output_json"], feature_data)

if __name__ == "__main__": main()
