import logging
from typing import List, Optional
import boto3

logger = logging.getLogger(__name__)
cloudwatch = boto3.client("cloudwatch")


class AgentMetrics:
    """Handles emitting CloudWatch metrics for agent usage"""

    @staticmethod
    def emit_agent_invocation(agent_name: str, duration_ms: int, success: bool, error_type: Optional[str] = None):
        """Emit metrics for a single agent invocation"""
        try:
            # Base dimensions for all metrics
            dimensions = [{"Name": "AgentName", "Value": agent_name}]

            # Add error type dimension if available
            if error_type and not success:
                error_dimensions = dimensions + [{"Name": "ErrorType", "Value": error_type}]
            else:
                error_dimensions = dimensions

            # Create metric data
            metric_data = [
                # Count total invocations
                {"MetricName": "AgentInvocationCount", "Dimensions": dimensions, "Unit": "Count", "Value": 1},
                # Track success rate
                {
                    "MetricName": "AgentSuccessCount",
                    "Dimensions": dimensions,
                    "Unit": "Count",
                    "Value": 1 if success else 0,
                },
                # Track latency
                {
                    "MetricName": "AgentLatency",
                    "Dimensions": dimensions,
                    "Unit": "Milliseconds",
                    "Value": float(duration_ms),
                },
            ]

            # Add error metrics if failed
            if not success:
                metric_data.append(
                    {"MetricName": "AgentErrorCount", "Dimensions": error_dimensions, "Unit": "Count", "Value": 1}
                )

            # Send metrics to CloudWatch
            cloudwatch.put_metric_data(Namespace="MySuperAgent/Agents", MetricData=metric_data)

        except Exception as e:
            logger.error(f"Failed to emit agent metrics: {str(e)}")

    @staticmethod
    def emit_delegator_metrics(duration_ms: int, success: bool, selected_agents: List[str], attempts: int):
        """Emit metrics for delegator operations"""
        try:
            # Base dimensions
            dimensions: List[dict] = []

            # Create metric data
            metric_data = [
                # Count delegator invocations
                {"MetricName": "DelegatorInvocationCount", "Dimensions": dimensions, "Unit": "Count", "Value": 1},
                # Track success rate
                {
                    "MetricName": "DelegatorSuccessCount",
                    "Dimensions": dimensions,
                    "Unit": "Count",
                    "Value": 1 if success else 0,
                },
                # Track latency
                {
                    "MetricName": "DelegatorLatency",
                    "Dimensions": dimensions,
                    "Unit": "Milliseconds",
                    "Value": float(duration_ms),
                },
                # Track retry attempts
                {
                    "MetricName": "DelegatorAttempts",
                    "Dimensions": dimensions,
                    "Unit": "Count",
                    "Value": float(attempts),
                },
            ]

            # Add metrics for each selected agent
            for idx, agent in enumerate(selected_agents[:3]):  # Only track top 3 selected agents
                position = idx + 1
                metric_data.append(
                    {
                        "MetricName": f"SelectedAgentPosition{position}",
                        "Dimensions": [{"Name": "AgentName", "Value": agent}],
                        "Unit": "Count",
                        "Value": 1,
                    }
                )

            # Send metrics to CloudWatch
            cloudwatch.put_metric_data(Namespace="MySuperAgent/Delegator", MetricData=metric_data)

        except Exception as e:
            logger.error(f"Failed to emit delegator metrics: {str(e)}")
