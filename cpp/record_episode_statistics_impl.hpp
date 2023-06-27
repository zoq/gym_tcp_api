/**
 * @file record_episode_statistics_impl.hpp
 * @author Nabanita Dash
 *
 * Implementation of miscellaneous record episode statistics routines.
 */
#ifndef GYM_RECORD_EPISODE_STATISTICS_IMPL_HPP
#define GYM_RECORD_EPISODE_STATISTICS_IMPL_HPP

// In case it hasn't been included yet.
#include "record_episode_statistics.hpp"
#include "messages.hpp"

namespace gym {

inline RecordEpisodeStatistics::RecordEpisodeStatistics()
{
  // Nothing to do here.
}

inline void RecordEpisodeStatistics::client(Client& c)
{
  clientPtr = &c;
}

inline void RecordEpisodeStatistics::start()
{
  clientPtr->send(messages::RecordEpisodeStatisticsStart());
}

} // namespace gym

#endif
