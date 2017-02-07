/**
 * @file parser.hpp
 * @author Marcus Edel
 *
 * Definition of miscellaneous parser routines.
 */
#ifndef GYM_PARSER_HPP
#define GYM_PARSER_HPP

#include <string>
#include <armadillo>

#include "rapidjson/document.h"

namespace gym {

using namespace rapidjson;


class Space;

/**
 * Definition of a parser class that is used to parse the reponses.
 */
class Parser
{
 public:
  /**
   * Create the Parser object.
   */
  Parser();

  /**
   * Create the Parser object using the specified json string and create the
   * tree to extract the attributes.
   *
   * @param data The data encoded as json string.
   */
  Parser(const std::string& data);

  /**
   * Parse the specified json string and create a tree to extract the
   * attributes.
   *
   * @param data The data encoded as json string.
   */
  void parse(const std::string& data);

  /**
   * Parse the observation data.
   *
   * @param space The space information class.
   * @param observation The parsed observation.
   */
  void observation(const Space* space, arma::mat& observation);

  /**
   * Parse the space data.
   *
   * @param space The space information class.
   */
  void space(Space* space);

  /**
   * Parse the action sample.
   *
   * @param space The space information class.
   * @param sample The parsed sample.
   */
  void actionSample(const Space* space, arma::mat& sample);

  /**
   * Parse the info data.
   *
   * @param reward The reward information.
   * @param done The information whether task succeed or not.
   */
  void info(double& reward, bool& done, std::string& info);

  /**
   * Parse the environment data.
   *
   * @param instance The instance identifier.
   */
  void environment(std::string& instance);

 private:
  //! Store results of the given json string in the row'th of the given
  //! matrix v.
  void vec(const Value& vector, arma::mat& v);

  //! Store results of the given json string in the row'th of the given
  //! matrix v.
  void vec(const Value& vector, std::vector<float>& v);

  //! Store results of the given json string in the row'th of the given
  //! matrix v.
  void vec(const Value& vector, std::vector<int>& v);

  //! Locally-stored document to parse the json string.
  Document document;
};

} // namespace gym


// Include implementation.
#include "parser_impl.hpp"

#endif