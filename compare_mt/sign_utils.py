########################################################################################
# Compare two systems using bootstrap resampling                                       #
#  adapted from https://github.com/neubig/util-scripts/blob/master/paired-bootstrap.py #
#                                                                                      #
# See, e.g. the following paper for references                                         #
#                                                                                      #
# Statistical Significance Tests for Machine Translation Evaluation                    #
# Philipp Koehn                                                                        #
# http://www.aclweb.org/anthology/W04-3250                                             #
#                                                                                      #
########################################################################################

import numpy as np
from compare_mt import scorers
import nltk

def eval_with_paired_bootstrap(ref, outs,
                               scorer,
                               compare_directions=[(0, 1)],
                               num_samples=1000, sample_ratio=0.5):
  """
  Evaluate with paired boostrap.
  This compares several systems, performing a signifiance tests with
  paired bootstrap resampling to compare the accuracy of the specified systems.
  
  Args:
    ref: The correct labels
    outs: The output of systems
    scorer: The scorer
    compare_directions: A string specifying which two systems to compare
    num_samples: The number of bootstrap samples to take
    sample_ratio: The ratio of samples to take every time

  Returns:
    A tuple containing the win ratios, statistics for systems
  """
  
  sys_scores = [[] for _ in outs] 
  wins = [[0, 0, 0] for _ in compare_directions]
  n = len(ref)
  ids = list(range(n))

  cache_stats = [scorer.cache_stats(ref, out) for out in outs] 

  for _ in range(num_samples):
    # Subsample the gold and system outputs
    np.random.shuffle(ids)
    reduced_ids = ids[:int(len(ids)*sample_ratio)]
    # Calculate accuracy on the reduced sample and save stats
    if cache_stats[0]:
      sys_score, _ = zip(*[scorer.score_cached_corpus(reduced_ids, cache_stat) for cache_stat in cache_stats])
    else:
      reduced_ref = [ref[i] for i in reduced_ids]
      reduced_outs = [[out[i] for i in reduced_ids] for out in outs]
      sys_score, _ = zip(*[scorer.score_corpus(reduced_ref, reduced_out) for reduced_out in reduced_outs])

    for i, compare_direction in enumerate(compare_directions): 
      left, right = compare_direction
      if sys_score[left] > sys_score[right]:
        wins[i][0] += 1
      if sys_score[left] < sys_score[right]:
        wins[i][1] += 1
      else:
        wins[i][2] += 1
    
    for i in range(len(outs)): 
      sys_scores[i].append(sys_score[i])

  # Print win stats
  wins = [[x/float(num_samples) for x in win] for win in wins]

  # Print system stats
  sys_stats = []
  for i in range(len(outs)): 
    sys_scores[i].sort()
    sys_stats.append({'mean':np.mean(sys_scores[i]), 'median':np.median(sys_scores[i]), 'lower_bound':sys_scores[i][int(num_samples * 0.025)], 'upper_bound':sys_scores[i][int(num_samples * 0.975)]})
 
  return wins, sys_stats

