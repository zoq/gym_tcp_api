/**
 * @file example.cpp
 * @author Marcus Edel
 *
 * Simple random agent.
 */

#include <iostream>

#include "environment.hpp"

using namespace gym;

int main(int argc, char* argv[])
{
  const std::string environment = "CartPole-v1";
  const std::string host = "127.0.0.1";
  const std::string port = "4040";
  const std::string render_mode = "human";

  double totalReward = 0;
  size_t totalSteps = 0;

  Environment env(host, port, environment, render_mode);
  env.compression(9);
  env.record_episode_stats.start();

  env.reset();
  env.render();

  while (1)
  {
    arma::mat action = env.action_space.sample();
    std::cout << "action: \n" << action << std::endl;

    env.step(action);

    totalReward += env.reward;
    totalSteps += 1;

    if (env.done)
    {
      break;
    }

    std::cout << "Current step: " << totalSteps << " current reward: "
      << totalReward << std::endl;
  }

  std::cout << "Instance: " << env.instance << " total steps: " << totalSteps
      << " reward: " << totalReward << std::endl;

  env.close();
  const std::string url = env.url();

  std::cout << "Video: https://kurg.org/media/gym/" << url
      << " (it might take some minutes before the video is accessible)."
      << std::endl;

  return 0;
}
