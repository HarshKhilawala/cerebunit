# ~/cerebtests/cerebunit/validation_tests/cells/Purkinje/test_for_soma_Rin.py
#
# =============================================================================
# test_for_soma_Rin.py 
#
# created 10 July 2019
# modified
#
# =============================================================================

import sciunit
import numpy
import quantities as pq

from cerebunit.capabilities.cells.measurements import ProducesEphysMeasurement
from cerebunit.statistics.data_conditions import NecessaryForHTMeans
from cerebunit.statistics.stat_scores import TScore # if NecessaryForHTMeans passes
from cerebunit.statistics.stat_scores import ZScoreForSignTest as ZScore
from cerebunit.statistics.hypothesis_testings import HtestAboutMeans, HtestAboutMedians

# to execute the model you must be in ~/cerebmodels
from executive import ExecutiveControl
from sciunit.scores import NoneScore#, ErrorScore

class SomaRinTest(sciunit.Test):
    """This test compares the measured resting Vm observed in real animal (in-vitro or in-vivo, depending on the data) generated from neuron against those by the model.

    About the test.
    ===============

    The test class has three levels of mechanisms.

    Level-1: :py:meth`.validate_observation`
    ----------------------------------------

    Given that the experimental/observed data has the following: __mean__, __SD__, __sample_size__, __units__, and __raw_data__, :py:meth`.validate_observation` checks for them. The method then checks the data condition by asking ``NecessaryForHTMeans``. Depending on the data condition the appropriate ``score_type`` is assigned and corresponding necessary parameter; for t-Test, the parameter ``observation["standard_error"]`` and for sign-Test, the parameter ``observation["median"]``.

    Level-2: :py:meth`.generate_prediction`
    ---------------------------------------

    The model is executed to get the model prediction. The prediction is a the resting Vm from the soma of a PurkinjeCell returned as a ``quantities.Quantity`` object.

    Level-3: :py:meths`.compute_score`
    ----------------------------------

    The prediction made by the model is then used as the __null value__ for the compatible ``score_type`` based on the ``datacond`` determined by :py:meth`.validate_observation`. The level ends by returning the compatible test-statistic (t or z-statistic) as a ``score``.

    How to use:
    ~~~~~~~~~~~

    ::
       from cerebunit.validation_tests.cells.Purkinje import SomaRinTest
       data = json.load(open("/home/main-dev/cerebdata/expdata/cells/PurkinjeCell/Llinas_Sugimori_1980_soma_Rin.json"))
       test = SomaRinTest( data )
       s = test.judge(chosenmodel, deep_error=True)

    Then to get the test score ``s.score`` and test report call ``print(s.description)``. If one is interested in getting the computed statistics call ``s.statistics``.

    Further notes on the test.
    ==========================

    * The experimental observation data (as __json__ file) must have the element __protocol_parameters__, which in turn has the nests the elements __temperature__ and __initial_resting_Vm__.
    * One should consider whether the model is compared against __in vitro__ or __in vivo__ experimental data (in addition to the species under study). For example,

       - Consider the Llinas and Sugimori (1980, 10.1113/jphysiol.1980.sp013357) experimental data (__Llinas_Sugimori_1980_soma_restVm.json__)
       - The reported experimental data only includes those with initial resting levels for >= -50 mV discarding those for < -50 mV.
       - The observed resting potential are claimed by the authors to be more negative than those observed in vivo.
       - The authors infer that this could be due to in vitro which is done on slices. The slicing removes background synaptic input generated by parallel fibre synapses.
       - __For more details see Llinas_Sugimori_1980_soma_restVm.json__

    """
    required_capabilities = (ProducesEphysMeasurement,)
    score_type = NoneScore # Placeholder which will be set at validate_observation

    def validate_observation(self, observation, first_try=True):
        """
        This function is called automatically by sciunit and
        clones it into self.observation
        This checks if the experimental_data is of some desired
        form or magnitude.
        Not exactly this function but a version of this is already
        performed by the ValidationTestLibrary.get_validation_test
        """
        print("Validate Observation ...")
        if ( "mean" not in observation or
             "SD" not in observation or
             "sample_size" not in observation or
             "units" not in observation or
             observation["units"] is not "Mohm" or
             "raw_data" not in observation or
             "protocol_parameters" not in observation or # these last two are required for
             "temperature" not in observation["protocol_parameters"] or # for running the
             "initial_resting_Vm" not in observation["protocol_parameters"] or # test correctly
             "current_amplitude" not in observation["protocol_parameters"] or
             "current_unit": not in observation["protocol_parameters"] or
             observation["protocol_parameters"]["current_unit"] is not "nA" ):
            raise sciunit.ObservationError
        self.observation = observation
        self.observation["units"] = "ohm"
        self.observation["mean"] = pq.Quantity( observation["mean"]*1E6,
                                                units=self.observation["units"] )
        self.observation["SD"] = pq.Quantity( observation["SD"]*1E6,
                                              units=self.observation["units"] )
        self.observation["raw_data"] = pq.Quantity( [ x*1E6 for x in observation["raw_data"] ],
                                                    units=self.observation["units"] )
        self.datacond = NecessaryForHTMeans.ask( observation["sample_size"],
                                                 self.observation["raw_data"] )
        if self.datacond==True:
            self.score_type = TScore
            self.observation["standard_error"] = \
                  pq.Quantity( observation["SD"] / numpy.sqrt(observation["sample_size"]),
                               units=observation["units"] )
        else:
            self.score_type = ZScore
            self.observation["median"] = numpy.median(self.observation["raw_data"])
        # parameters for properly running the test
        self.observation["celsius"] = observation["protocol_parameters"]["temperature"]
        self.observation["v_init"] = observation["protocol_parameters"]["initial_resting_Vm"]
        self.observation["amp"] = observation["protocol_parameters"]["current_amplitude"]
        #
        print("Validated.")

    def generate_prediction(self, model, verbose=False):
        """
        Generates resting Vm from soma.
        The function is automatically called by sciunit.Test which this test is a child of.
        Therefore as part of sciunit generate_prediction is mandatory.
        """
        #self.confidence = confidence # set confidence for test 90%, 95% (default), 99%
        #
        print("Testing ...")
        runtimeparam = {"dt": 0.025, "celsius": self.observation["celsius"],
                        "tstop": 500.0, "v_init": self.observation["v_init"]}
        stimparam = {"type": ["current", "IClamp"],
                 "stimlist": [ {"amp": self.observation["amp"], "dur": 200.0, "delay": 400.0},
                               {"amp": 0.0, "dur": 200.0, "delay": 400.0+200.},
                               {"amp": self.observation["amp"], "dur": 200.0, "delay": 600.0+200.0],
                    "tstop": runtimeparam["tstop"] }
        ec = ExecutiveControl()
        #ec.chosenmodel = model
        #ec.chosenmodel.restingVm = \
        model = ec.launch_model( parameters = runtimeparam, stimparameters = stimparam,
                                 stimloc = model.cell.soma, onmodel = model,
                                 capabilities = {"model": "produce_soma_inputR",
                                                 "vtest": ProducesEphysMeasurement},
                                 mode = "capability" )
        return pq.Quantity( numpy.mean(model.prediction), # prediction
                            units = self.observation["units"] )

    def compute_score(self, observation, prediction, verbose=False):
        """
        This function like generate_pediction is called automatically by sciunit
        which RestingVmTest is a child of. This function must be named compute_score
        The prediction processed from "vm_soma" is compared against
        the experimental_data to get the binary score; 0 if the
        prediction correspond with experiment, else 1.
        """
        print("Computing score ...")
        #print(observation == self.observation) # True
        if self.datacond==True:
            x = TScore.compute( observation, prediction  )
            hypoT = HtestAboutMeans( self.observation, prediction, x )
            score = TScore(x)
            score.description = hypoT.outcome
            score.statistics = hypoT.statistics
        else:
            x = ZScore.compute( observation, prediction )
            hypoT = HtestAboutMedians( self.observation, prediction, x )
            score = ZScore(x)
            score.description = hypoT.outcome
            score.statistics = hypoT.statistics
        print("Done.")
        print(score.description)
        return score

