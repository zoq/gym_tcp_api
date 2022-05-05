/**
 * @file record_episode_statistics.hpp
 * @author Nabanita Dash
 *
 * Definition of miscellaneous record episode statistics routines.
 */
#ifndef GYM_RECORD_EPISODE_STATISTICS_HPP
#define GYM_RECORD_EPISODE_STATISTICS_HPP

#include "client.hpp"

namespace gym {


/*
 * Definition of the  class.
 */
class RecordEpisodeStatistics
{
 public:
  /**
   * Create the Parser object.
   */
  RecordEpisodeStatistics();

  /**
   * Set the client which is connected with the server.
   *
   * @param c The client object which is connected with the server.
   */
  void client(Client& c);

  /*
   * Start the using the specified parameter.
   */
  void start();

private:
  //! Locally-stored client pointer used to communicate with the connected
  //! server.
  Client* clientPtr;
};
} // namespace gym

// Include implementation.
#include "record_episode_statistics_impl.hpp"

#endif