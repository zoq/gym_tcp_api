#include <cmath>
#include <mlpack/core.hpp>
#include <mlpack/core/optimizers/sgd/sgd.hpp>
#include <mlpack/methods/ann/layer/layer.hpp>
#include <mlpack/methods/ann/init_rules/zero_init.hpp>
#include <mlpack/methods/ann/ffn.hpp>
#include <mlpack/methods/ann/layer/linear.hpp>
#include <mlpack/methods/ann/layer/dropout.hpp>
#include <mlpack/methods/ann/layer/leaky_relu.hpp>
#include <mlpack/methods/ann/layer/convolution.hpp>

using namespace mlpack;
using namespace optimization;
using namespace ann;
using namespace gym;

class Agent{
 public:
  FFN<MeanSquaredError<>, ZeroInitialization> model;
  
  Agent(size_t inputW, size_t inputH){
    // 3 stream to 4 streams of depth, filter 4x4
    model.Add<Convolution<>>(3, 4, 4, 4, 1, 1, 0, 0, inputW, inputH);
    model.Add<LeakyReLU<>>();
    
    // 4 depth to 5 depth, filter 4x4, strides of 2
    model.Add<Convolution<>>(4, 5, 4, 4, 3, 3, 0, 1);
    model.Add<LeakyReLU<>>();

    model.Add<Linear<>>(17680, 700);
    model.Add<LeakyReLU<>>();
    
    // Fully Connected from 700 -> 6 nodes
    model.Add<Linear<>>(700, 6);
    model.Add<LeakyReLU<>>();
  }

  void Play(Environment& env, double explore){
    arma::mat result, actionMat, frame;
    double maxRewardAction;

    double instinct = 0.0001;

    double totalReward = 0;
    size_t totalSteps = 0;

    while(1){
      //Get observation
      frame = arma::vectorise(env.observation);
      
      //Predict a reward for each action in current frame
      model.Predict(frame, result);
      
      if(arma::randu() > explore){
        //Pick the action with maximum reward
        maxRewardAction = arma::mat(result.t()).index_max();
      }
      else{
        //Pick random action number
        maxRewardAction = floor(arma::randu() * 6);
      }

      //Make 1 hot vector for chosen action
      actionMat = maxRewardAction;

      std::cout << "Action: " << actionMat << std::endl;

      env.step(actionMat);

      // New Matrix for correct result
      // replace current reward with correct one
      arma::mat correctResult(result);
      correctResult[maxRewardAction] = env.reward - totalReward;

      // Optimize for the correct result given same frame

      std::cout << "Corrected result:";
      for(int i : correctResult){
        std::cout << i << " ";
      }
      std::cout << std::endl;

      model.Train(std::move(frame), std::move(correctResult));
      
      if(env.done){
        break;
      }

      totalReward += env.reward;
      totalSteps += 1;
      explore -= instinct;

      std::cout << "Current step: " << totalSteps << " current reward: "
      << totalReward << std::endl;
    }
  }

};