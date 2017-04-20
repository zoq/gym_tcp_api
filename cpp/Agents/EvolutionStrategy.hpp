#include <iostream>
#include <vector>
#include <string>
#include <mlpack/core.hpp>
#include <mlpack/core/optimizers/sgd/sgd.hpp>
#include "../environment.hpp"

using namespace mlpack;
using namespace std;
using namespace arma;
using namespace gym;

class EvolutionStrategyAgent{
 public:
  mat model;
  size_t frameW, frameH, num_actions;

  EvolutionStrategyAgent(size_t frameW,
                    size_t frameH,
                    size_t num_actions)
  :
  frameW(frameW),
  frameH(frameH),
  num_actions(num_actions)
  {
    model = randu(num_actions, frameW * frameH * 3);
  }

  void Play(string environment,
            string host,
            string port)
  {
    size_t num_workers = 5;
    double sigma = 1; // Rewards standard deviation
    double alpha = 0.005; // Learning Rate
    size_t input = frameW * frameH * 3;
    
    mat workerRewards(num_workers, 1);
    vector<mat> epsilons(num_workers);

    while(1)
    {
      #pragma omp parallel for
      for(size_t i = 0; i < num_workers; i++)
      {
        mat epsilon = randn(num_actions, input);
        mat innerModel = model + (sigma * epsilon);

        epsilons[i] = epsilon;

        Environment env(host, port, environment);
        
        env.compression(9);
        
        // Create a folder for Agent Files
        string folder("./dummy/");
        folder += i + '/';

        // Monitor its moves
        env.monitor.start(folder, true, false);

        env.reset();
        env.render();

        size_t totalReward = 0;

        //Until the episode is complete
        while(1)
        {
          mat maxAction;
          mat action =  innerModel * vectorise(env.observation);

          maxAction = action.index_max();

          env.step(maxAction);

          totalReward += env.reward;

          if (env.done)
          {
            break;
          }
        }
        
        env.close();

        workerRewards[i] = totalReward;
      }

      mat sumRxEpsilon = zeros(num_actions, input);

      for(size_t i = 0; i < num_workers; i++){
        mat stdReward = (workerRewards[i] -
                            mean(workerRewards)) /
                            stddev(workerRewards);
        
        sumRxEpsilon += epsilons[i] * as_scalar(stdReward);
      }

      model = model + (alpha/(num_workers * sigma)) * sumRxEpsilon;

      cout << "Worker Rewards: ";
      for(double reward : workerRewards){
        cout << reward << " ";
      }
      cout << "\n";
    }
  }
};
