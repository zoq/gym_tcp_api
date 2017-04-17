#include "EvolutionStrategy.hpp"

int main(int argc, char* argv[]){
  const std::string environment = "SpaceInvaders-v0";
  const std::string host = "127.0.0.1"/*"kurg.org"*/;
  const std::string port = "4040";

  EvolutionStrategyAgent agent(210, 160, 6);

  agent.Play(environment, host, port);

  return 0;
}