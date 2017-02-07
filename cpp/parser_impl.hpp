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
  document.Parse(data.c_str());

  parse(data);
}

void Parser::parse(const std::string& data)
{
  document.Parse(data.c_str());
}

void Parser::actionSample(const Space* space, arma::mat& sample)
{
  if (space->type == Space::DISCRETE)
  {
    if (sample.is_empty())
    {
      sample = arma::mat(1, 1);
    }

    sample(0) = document["sample"].GetDouble();
  }
}

void Parser::info(double& reward, bool& done, std::string& info)
{
  for (Value::ConstMemberIterator itr = document.MemberBegin();
    itr != document.MemberEnd(); ++itr)
  {
    std::string key = itr->name.GetString();

    if (key == "reward")
    {
      reward = itr->value.GetDouble();
    }
    else if (key == "done")
    {
      done = itr->value.GetBool();
    }
    else if (key == "info")
    {
      info = "";
      for (auto& m : itr->value.GetObject())
      {
        info += " " + std::string(m.name.GetString());
      }
    }
  }
}

void Parser::environment(std::string& instance)
{
  for (Value::ConstMemberIterator itr = document.MemberBegin();
    itr != document.MemberEnd(); ++itr)
  {
    std::string key = itr->name.GetString();

    if (key == "instance")
    {
      instance = itr->value.GetString();
    }
  }
}

void Parser::observation(const Space* space, arma::mat& observation)
{
  if (space->boxShape.size() == 1)
  {
    observation = arma::mat(space->boxShape[0], 1);
    const rapidjson::Value& array1 = document["observation"];
    vec(array1, observation);
  }
  else if (space->boxShape.size() == 2)
  {
    observation = arma::mat(space->boxShape[1], space->boxShape[0]);

    size_t elem = 0;
    const rapidjson::Value& array1 = document["observation"];
    for (rapidjson::SizeType i = 0; i < array1.Size(); i++)
    {
      const rapidjson::Value& array2 = array1[i];
      for (rapidjson::SizeType j = 0; j < array2.Size(); j++)
      {
        observation(elem++) = array2[j].GetDouble();
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
    const rapidjson::Value& array1 = document["observation"];
    for (rapidjson::SizeType i = 0; i < array1.Size(); i++)
    {
      const rapidjson::Value& array2 = array1[i];
      for (rapidjson::SizeType j = 0; j < array2.Size(); j++)
      {
        size_t z = 0;
        const rapidjson::Value& array3 = array2[j];
        for (rapidjson::SizeType k = 0; k < array3.Size(); k++, elem++, z++)
        {
          elem = elem % observation.n_rows;
          temp.slice(z)(elem) = array3[k].GetDouble();
        }
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
  for (Value::ConstMemberIterator itr = document["info"].MemberBegin();
    itr != document["info"].MemberEnd(); ++itr)
  {
    std::string key = itr->name.GetString();

    if (key == "name")
    {
      std::string value = itr->value.GetString();

      if (value == "MultiDiscrete")
      {
        space->type = Space::MULTIDISCRETE;
      }
      else if (value == "Discrete")
      {
        space->type = Space::DISCRETE;
      }
      else if (value == "Box")
      {
        space->type = Space::BOX;
      }
    }
    else if (key == "n")
    {
      space->n = itr->value.GetInt();
    }
    else if (key == "high")
    {
      vec(itr->value, space->boxHigh);
    }
    else if (key == "low")
    {
      vec(itr->value, space->boxLow);
    }
    else if (key == "shape")
    {
      vec(itr->value, space->boxShape);
    }
  }
}

void Parser::vec(const Value& vector, arma::mat& v)
{
  size_t idx = 0;
  for (auto& elem : vector.GetArray())
  {
    v(idx++) = elem.GetDouble();
  }
}

void Parser::vec(const Value& vector, std::vector<float>& v)
{
  for (auto& elem : vector.GetArray())
  {
    v.push_back(elem.GetFloat());
  }
}

void Parser::vec(const Value& vector, std::vector<int>& v)
{
  for (auto& elem : vector.GetArray())
  {
    v.push_back(elem.GetInt());
  }
}

} // namespace gym

#endif