// Copyright 2023 Eugen Kaltenegger

#include <gtest/gtest.h>
#include <tuw_geometry/point2d.h>
#include "tuw_iwos_tools/icc_calculator.h"
#include "tuw_iwos_tools/side.h"

using tuw_iwos_tools::Side;
using tuw_iwos_tools::IccCalculator;

class IccCalculatorTest : public ::testing::Test
{
protected:
  double wheelbase_{0.5};
  double wheeloffset_{0.1};
  double revolute_velocity_tolerance_{0.1};
  double steering_position_tolerance_{0.1};
  std::unique_ptr<IccCalculator> icc_calculator_ = std::make_unique<IccCalculator>(this->wheelbase_,
                                                                                   this->wheeloffset_,
                                                                                   this->revolute_velocity_tolerance_,
                                                                                   this->steering_position_tolerance_);
  std::map<Side, double> revolute_velocity_;
  std::map<Side, double> steering_position_;
  std::shared_ptr<tuw::Point2D> icc_ = std::make_shared<tuw::Point2D>(0.0, 0.0, 0.0);
  std::shared_ptr<std::map<Side, double>> radius_ = std::make_shared<std::map<Side, double>>();
};

TEST_F(IccCalculatorTest, vector_side_test_generic_left)
{
  tuw::Pose2D wheel (0.0, 0.0, -M_PI / 8);
  tuw::Point2D icc (1.0, 0.0);
  ASSERT_EQ(IccCalculator::vectorSide(wheel, icc), Side::LEFT);
}

TEST_F(IccCalculatorTest, vector_side_test_generic_right)
{
  tuw::Pose2D wheel (0.0, 0.0, M_PI / 8);
  tuw::Point2D icc (1.0, 0.0);
  ASSERT_EQ(IccCalculator::vectorSide(wheel, icc), Side::RIGHT);
}

TEST_F(IccCalculatorTest, vector_side_test_forward_icc_left)
{
  tuw::Pose2D wheel (0.0, 0.25, 0.0);
  tuw::Point2D icc (0.0, 1.0);
  ASSERT_EQ(IccCalculator::vectorSide(wheel, icc), Side::LEFT);
}

TEST_F(IccCalculatorTest, vector_side_test_forward_icc_right)
{
  tuw::Pose2D wheel (0.0, -0.25, 0.0);
  tuw::Point2D icc (0.0, -1.0);
  ASSERT_EQ(IccCalculator::vectorSide(wheel, icc), Side::RIGHT);
}

TEST_F(IccCalculatorTest, vector_side_test_backward_icc_left)
{
  tuw::Pose2D wheel (0.0, 0.25, M_PI_2);
  tuw::Point2D icc (0.0, 1.0);
  ASSERT_EQ(IccCalculator::vectorSide(wheel, icc), Side::LEFT);
}

TEST_F(IccCalculatorTest, vector_side_test_backward_icc_right)
{
  tuw::Pose2D wheel (0.0, -0.25, M_PI_2);
  tuw::Point2D icc (0.0, -1.0);
  ASSERT_EQ(IccCalculator::vectorSide(wheel, icc), Side::RIGHT);
}

TEST_F(IccCalculatorTest, icc_standing)
{
  this->revolute_velocity_[Side::LEFT ] = 0.0;
  this->revolute_velocity_[Side::RIGHT] = 0.0;
  this->steering_position_[Side::LEFT ] = 0.0;
  this->steering_position_[Side::RIGHT] = 0.0;

  this->icc_calculator_->calculateIcc(this->revolute_velocity_, this->steering_position_, this->icc_, this->radius_);

  ASSERT_EQ(this->icc_->x(), std::numeric_limits<double>::infinity());
  ASSERT_EQ(this->icc_->y(), std::numeric_limits<double>::infinity());

  ASSERT_EQ(this->radius_->at(Side::LEFT  ), std::numeric_limits<double>::infinity());
  ASSERT_EQ(this->radius_->at(Side::RIGHT ), std::numeric_limits<double>::infinity());
  ASSERT_EQ(this->radius_->at(Side::CENTER), std::numeric_limits<double>::infinity());
}