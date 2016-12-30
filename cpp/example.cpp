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
  const std::string environment = "CartPole-v0";
  const std::string host = "127.0.0.1";
  const std::string port = "4040";

  double totalReward = 0;
  size_t totalSteps = 0;

  Environment env(host, port, environment);
  env.reset();

  while (1)
  {
    env.step(env.action_space.sample());
    env.render();
    totalReward += env.reward;
    totalSteps += 1;

    if (env.done)
    {
      break;
    }
  }

  std::cout << "Total steps: " << totalSteps << " reward: " << totalReward
      << std::endl;

  return 0;
}
