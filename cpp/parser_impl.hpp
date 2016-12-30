/**
 * @file parser_impl.hpp
 * @author Marcus Edel
 *
 * Implementation of miscellaneous parser routines.
 */
#ifndef GYM_PARSER_IMPL_HPP
#define GYM_PARSER_IMPL_HPP

// In case it hasn't been included yet.
#include "parser.hpp"
#include "space.hpp"

namespace gym {

Parser::Parser()
{
  // Nothing to do here.
}

Parser::Parser(const std::string& data)
{
  parse(data);
}

void Parser::parse(const std::string& data)
{
  std::stringstream ss(data);
  boost::property_tree::read_json(ss, pt);
}

void Parser::actionSample(const Space* space, arma::mat& sample)
{
  if (space->type == Space::DISCRETE)
  {
    if (sample.is_empty())
    {
      sample = arma::mat(1, 1);
    }

    for (ptree::const_iterator it = pt.begin(); it != pt.end(); ++it)
    {
      sample(0) = it->second.get_value<int>();
    }
  }
}

void Parser::info(double& reward, bool& done, std::string& info)
{
  for (ptree::const_iterator it = pt.begin();
      it != pt.end(); ++it)
  {
    if (std::string(it->first) == "reward")
    {
      reward = it->second.get_value<float>();
    }
    else if (std::string(it->first) == "done")
    {
      done = it->second.get_value<bool>();
    }
    else if (std::string(it->first) == "info")
    {
      info = it->second.get_value<std::string>();
    }
  }
}

void Parser::observation(const Space* space, arma::mat& observation)
{
  if (space->boxShape.size() == 1)
  {
    observation = arma::mat(space->boxShape[0], 1);
    vec(pt, "observation", observation);
  }
  else if (space->boxShape.size() == 2)
  {
    observation = arma::mat(space->boxShape[1], space->boxShape[0]);

    size_t elem = 0;
    for (ptree::value_type &row : pt.get_child("observation"))
    {
        int y = 0;
        for (ptree::value_type &cell : row.second)
        {
            observation(elem++) = cell.second.get_value<float>();
        }
    }

    observation = observation.t();
  }
  else if (space->boxShape.size() == 3)
  {
    arma::cube temp(space->boxShape[1], space->boxShape[0], space->boxShape[2]);
    observation = arma::mat(space->boxShape[0] * space->boxShape[1],
        space->boxShape[2]);

    size_t elem = 0;
    for (ptree::value_type &row : pt.get_child("observation"))
    {
        for (ptree::value_type &cellO : row.second)
        {
          size_t z = 0;
          for (ptree::value_type &cellI : cellO.second)
          {
            temp.slice(z)(elem) = cellI.second.get_value<float>();
          }

          elem++;
        }
    }

    for (size_t i = 0; i < space->boxShape[2]; ++i)
    {
      arma::mat slice = arma::trans(temp.slice(i));
      observation.col(i) = arma::vectorise(slice);
    }
  }
}

void Parser::space(Space* space)
{
  ptree::const_iterator end = pt.get_child("info").end();

  for (ptree::const_iterator it = pt.get_child("info").begin();
      it != end; ++it)
  {
    if (std::string(it->first) == "name")
    {
      if (it->second.get_value<std::string>() == "MultiDiscrete")
      {
        space->type = Space::MULTIDISCRETE;
      }
      else if (it->second.get_value<std::string>() == "Discrete")
      {
        space->type = Space::DISCRETE;
      }
      else if (it->second.get_value<std::string>() == "Box")
      {
        space->type = Space::BOX;
      }
    }
    else if (std::string(it->first) == "n")
    {
      space->n = it->second.get_value<int>();
    }
    else if (std::string(it->first) == "high")
    {
      vec(it->second, it->second.get_value<std::string>(), space->boxHigh);
    }
    else if (std::string(it->first) == "low")
    {
      vec(it->second, it->second.get_value<std::string>(), space->boxLow);
    }
    else if (std::string(it->first) == "shape")
    {
      vec(it->second, it->second.get_value<std::string>(), space->boxShape);
    }
  }
}

void Parser::vec(
    const ptree& pt, const ptree::key_type& key, arma::mat& v, int row)
{
  int col = 0;
  for (auto& item : pt.get_child(key))
  {
    v(row, col++) = item.second.get_value<int>();
  }
}

void Parser::vec(const ptree& pt, const std::string& key, arma::mat& v)
{
  int elem = 0;
  for (auto& item : pt.get_child(key))
  {
    v(elem++) = item.second.get_value<float>();
  }
}

void Parser::vec(
    const ptree& pt, const ptree::key_type& key, std::vector<float>& v)
{
  int col = 0;
  for (auto& item : pt.get_child(key))
  {
    v.push_back(item.second.get_value<float>());
  }
}

void Parser::vec(
    const ptree& pt, const ptree::key_type& key, std::vector<int>& v)
{
  int col = 0;
  for (auto& item : pt.get_child(key))
  {
    v.push_back(item.second.get_value<int>());
  }
}

} // namespace gym

#endif