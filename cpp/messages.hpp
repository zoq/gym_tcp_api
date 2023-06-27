/**
 * @file messages.hpp
 * @author Marcus Edel
 *
 * Miscellaneous messages.
 */
#ifndef GYM_MESSAGES_HPP
#define GYM_MESSAGES_HPP

#include <string>
#include <armadillo>

#include "space.hpp"

namespace gym {
namespace messages {

//! Create message to set the enviroment name.
static inline std::string EnvironmentName(const std::string& name)
{
  return "{\"env\":{\"name\": \"" + name + "\"}}";
}

//! Create message to reset the enviroment.
static inline std::string EnvironmentReset()
{
  return "{\"env\":{\"action\": \"reset\"}}";
}

//! Create message to start the Record Episode Statistics.
static inline std::string RecordEpisodeStatisticsStart()
{
  return "{\"record_episode_stats\":{\"action\": \"start\"}}";
}

//! Create message to set the compression level.
static inline std::string ServerCompression(const size_t compression)
{
  return "{\"server\":{\"compression\": \"" +
      std::to_string(compression) + "\"}}";
}

//! Create message to set the enviroment seed.
static inline std::string EnvironmentSeed(const size_t seed)
{
  return "{\"env\":{\"seed\": \"" + std::to_string(seed) + "\"}}";
}

//! Create message to close the enviroment.
static inline std::string EnvironmentClose()
{
  return "{\"env\":{\"action\": \"close\"}}";
}

//! Create message to get the action space.
static inline std::string EnvironmentActionSpace()
{
  return "{\"env\":{\"action\": \"actionspace\"}}";
}

//! Create message to get the observation space.
static inline std::string EnvironmentObservationSpace()
{
  return "{\"env\":{\"action\": \"observationspace\"}}";
}

//! Create message to get the action space sample.
static inline std::string EnvironmentActionSpaceSample()
{
  return "{\"env\":{\"actionspace\": \"sample\"}}";
}

//! Create message to get the action space.
static inline std::string Step(
    const arma::mat& action, Space& space, const bool render)
{
  if (space.type == Space::DISCRETE)
  {
    arma::mat actionTmp = action;
    if (action.n_elem > 1)
    {
      actionTmp(0) = arma::as_scalar(arma::find(action.max() == action, 1));
    }

    return "{\"step\":{\"action\":" + std::to_string((int) actionTmp(0)) +
      ", \"render\":" + std::to_string(render) + "}}";
  }
  if (space.type == Space::MULTIDISCRETE)
  {
    std::string actionStr = "[";
    for (size_t i = 0; i < action.n_elem; ++i)
    {
      if (i < (action.n_elem - 1))
      {
        actionStr += std::to_string((int) action(i)) + ",";
      }
      else
      {
        actionStr += std::to_string((int) action(i));
      }
    }
    actionStr += "]";

    std::string msg = "{\"step\":{\"action\":" + actionStr +
        ", \"render\":" + std::to_string(render) + "}}";

    return msg;
  }
  if (space.type == Space::BOX)
  {
    std::string actionStr = "[";
    for (size_t i = 0; i < action.n_elem; ++i)
    {
      if (i < (action.n_elem - 1))
      {
        actionStr += std::to_string((double) action(i)) + ",";
      }
      else
      {
        actionStr += std::to_string((double) action(i));
      }
    }
    actionStr += "]";

    std::string msg = "{\"step\":{\"action\":" + actionStr +
        ", \"render\":" + std::to_string(render) + "}}";

    return msg;
  }
  return "";
}

//! Create message to get the url.
static inline std::string URL()
{
  return "{\"url\":{\"action\": \"url\"}}";
}

} // namespace messages
} // namespace gym

#endif
