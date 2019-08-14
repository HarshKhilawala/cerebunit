# ============================================================================
# ~/cerebtests/cerebunit/stat_scores/zSignScore.py
#
# created 6 March 2019 Lungsi
#
# This py-file contains custum score functions initiated by
#
# from cerebunit import scoreScores
# from cerebunit.scoreScores import ABCScore
# ============================================================================

import numpy as np
import sciunit


# ==========================ZScoreForSignTest==================================
class ZScoreForSignTest(sciunit.Score):
    """
    Compute z-statistic for Sign Test.

    .. table:: Title here

    ================= ========================================================================
      Definitions      Interpretation                    
    ================= ========================================================================
     :math:`e_0`       some specified value              
     :math:`s_{+}`     number of values in sample :math:`> e_0`
     :math:`s_{-}`     number of values in sample :math:`< e_0`
     :math:`n_u`       number of values in sample :math:`\\neq e_0`
     z-statistic, z    z = :math:`\\frac{ s_{+} - \\frac{n_u}{2} }{ \\sqrt{\\frac{n_u}{4}} }`
    ================= ========================================================================
    
    **Use Case:**

    ::

      x = ZScoreForSignTest.compute( observation, prediction )
      score = ZScoreForSignTest(x)

    *Note*: As part of the `SciUnit <http://scidash.github.io/sciunit.html>`_ framework this custom :py:class:`.TScore` should have the following methods,

    * :py:meth:`.compute` (class method)
    * :py:meth:`.sort_key` (property)
    * :py:meth:`.__str__`

    """
    #_allowed_types = (float,)
    _description = ( "ZScoreForSignTest gives the z-statistic applied to medians. "
                   + "The experimental data (observation) is taken as the sample. "
                   + "The sample statistic is 'median' or computed median form 'raw_data'. "
                   + "The null-value is the 'some' specified value whic is taken to be the predicted value generated from running the model. " )

    @classmethod
    def compute(self, observation, prediction):
        """
        *Note:*

        * observation (sample) is in dictionary form with keys mean and
        * standard_error whose value has magnitude and python quantity
        * the populations parameter is the predicted value

        """
        data = np.array( observation["raw_data"] )
        splus = ( data < prediction ).sum()
        n_u = (data != prediction ).sum()
        self.score = (splus - (n_u/2)) / np.sqrt(n_u/4)
        return self.score # z_statistic

    @property
    def sort_key(self):
        return self.score

    def __str__(self):
        return "ZScore is " + str(self.score)
# ============================================================================
