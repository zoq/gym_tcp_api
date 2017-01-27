/**
 * @file environment_impl.hpp
 * @author Marcus Edel
 *
 * Implementation of miscellaneous environment routines.
 */
#ifndef GYM_ENVIRONMENT_IMPL_HPP
#define GYM_ENVIRONMENT_IMPL_HPP

// In case it hasn't been included yet.
#include "environment.hpp"
#include "messages.hpp"

namespace gym {

Environment::Environment() : renderValue(false)
{
  // Nothing to do here.
}

Environment::Environment(const std::string& host, const std::string& port) :
    renderValue(false)
{
  client.connect(host, port);
}

Environment::Environment(
    const std::string& host,
    const std::string& port,
    const std::string& environment) :
    renderValue(false)
{
  client.connect(host, port);
  make(environment);
}

void Environment::make(const std::string& environment)
{
  client.send(messages::EnvironmentName(environment));

  observationSpace();
  actionSpace();

  observation_space.client(client);
  action_space.client(client);
  monitor.client(client);
}

void Environment::render()
{
  if (renderValue)
  {
    renderValue = false;
  }
  else
  {
    renderValue = true;
  }
}

void Environment::close()
{
  client.send(messages::EnvironmentClose());
}

const arma::mat& Environment::reset()
{
  client.send(messages::EnvironmentReset());

  std::string json;
  client.receive(json);

  parser.parse(json);
  parser.observation(&observation_space, observation);

  return observation;
}

void Environment::step(const arma::mat& action)
{
  client.send(messages::Step(action, action_space, renderValue));

  std::string json;
  client.receive(json);

  parser.parse(json);
  parser.observation(&observation_space, observation);
  parser.info(reward, done, info);
}

void Environment::seed(const size_t s)
{
  client.send(messages::EnvironmentSeed(s));
}

void Environment::compression(const size_t compression)
{
  client.compression(compression);
  client.send(messages::ServerCompression(compression));
}

void Environment::observationSpace()
{
  client.send(messages::EnvironmentObservationSpace());

  std::string json;
  client.receive(json);

  parser.parse(json);
  parser.space(&observation_space);
}

void Environment::actionSpace()
{
  client.send(messages::EnvironmentActionSpace());

  std::string json;
  client.receive(json);

  parser.parse(json);
  parser.space(&action_space);
}

} // namespace gym

#endif