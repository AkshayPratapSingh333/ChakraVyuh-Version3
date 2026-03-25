"""
Demo: Simple federated learning simulation with visualization.
Run this to see Phase 2 in action!
"""

import sys
from pathlib import Path
import json
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from phase2_federated.federated_config import FederatedConfig, AggregationStrategy
from phase2_federated.federated_trainer import FederatedTrainer


def demo_basic_federated_learning():
    """
    Demo 1: Basic federated learning with 3 nodes and 5 rounds.
    """
    print("\n" + "="*70)
    print("DEMO 1: Basic Federated Learning")
    print("="*70)
    
    # Create config
    config = FederatedConfig(
        num_rounds=5,
        num_nodes=3,
        local_epochs=2,
        learning_rate=0.01,
        aggregation_strategy=AggregationStrategy.FED_AVG,
    )
    
    # Create trainer
    trainer = FederatedTrainer(config)
    
    # Train
    round_metrics = trainer.train()
    
    # Print summary
    summary = trainer.get_summary()
    print("\n" + "="*70)
    print("TRAINING SUMMARY")
    print("="*70)
    print(f"Rounds:                    {summary['num_rounds']}")
    print(f"Nodes:                     {summary['num_nodes']}")
    print(f"Aggregation Strategy:      {summary['aggregation_strategy']}")
    print(f"Best Accuracy:             {summary['best_accuracy']:.4%} (round {summary['best_round']})")
    print(f"Final Accuracy:            {summary['final_accuracy']:.4%}")
    print(f"Accuracy Improvement:      {summary['avg_accuracy_improvement']:.2f}%")
    
    # Save report
    report_path = trainer.save_training_report(
        "./phase2_federated/demo_results/federated_training_basic.json"
    )
    
    return trainer, report_path


def demo_aggregation_strategies():
    """
    Demo 2: Compare different aggregation strategies.
    """
    print("\n" + "="*70)
    print("DEMO 2: Comparing Aggregation Strategies")
    print("="*70)
    
    strategies = [
        AggregationStrategy.FED_AVG,
        AggregationStrategy.WEIGHTED_AVG,
        AggregationStrategy.MEDIAN,
    ]
    
    results = {}
    
    for strategy in strategies:
        print(f"\n--- Testing {strategy.value.upper()} ---")
        
        config = FederatedConfig(
            num_rounds=3,
            num_nodes=4,
            local_epochs=1,
            aggregation_strategy=strategy,
        )
        
        trainer = FederatedTrainer(config)
        trainer.train()
        
        summary = trainer.get_summary()
        results[strategy.value] = summary
        
        print(f"Best Accuracy: {summary['best_accuracy']:.4%}")
    
    # Compare results
    print("\n" + "="*70)
    print("STRATEGY COMPARISON")
    print("="*70)
    print(f"{'Strategy':<20} {'Best Accuracy':<20} {'Avg Improvement':<20}")
    print("-"*60)
    
    for strategy, result in results.items():
        print(
            f"{strategy:<20} {result['best_accuracy']:>18.4%} "
            f"{result['avg_accuracy_improvement']:>18.2f}%"
        )
    
    # Save comparison
    comparison_path = Path("./phase2_federated/demo_results/strategy_comparison.json")
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(comparison_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nComparison saved to {comparison_path}")
    
    return results


def demo_differential_privacy():
    """
    Demo 3: Federated learning with differential privacy.
    """
    print("\n" + "="*70)
    print("DEMO 3: Federated Learning with Differential Privacy")
    print("="*70)
    
    config = FederatedConfig(
        num_rounds=3,
        num_nodes=3,
        local_epochs=1,
        differential_privacy=True,
        dp_epsilon=1.0,
        dp_delta=0.01,
        clip_weights=True,
        weight_clip_norm=1.0,
    )
    
    trainer = FederatedTrainer(config)
    trainer.train()
    
    summary = trainer.get_summary()
    
    print("\n" + "="*70)
    print("DIFFERENTIAL PRIVACY SUMMARY")
    print("="*70)
    print(f"Differential Privacy:  ENABLED")
    print(f"Epsilon (ε):           {config.dp_epsilon}")
    print(f"Delta (δ):             {config.dp_delta}")
    print(f"Weight Clipping:       ENABLED (norm={config.weight_clip_norm})")
    print(f"\nBest Accuracy:         {summary['best_accuracy']:.4%}")
    print(f"Final Accuracy:        {summary['final_accuracy']:.4%}")
    
    return trainer


def demo_scaling():
    """
    Demo 4: Scaling federated learning to more nodes.
    """
    print("\n" + "="*70)
    print("DEMO 4: Scaling to Multiple Nodes")
    print("="*70)
    
    node_counts = [2, 4, 6]
    results = {}
    
    for num_nodes in node_counts:
        print(f"\n--- Training with {num_nodes} nodes ---")
        
        config = FederatedConfig(
            num_rounds=3,
            num_nodes=num_nodes,
            local_epochs=1,
        )
        
        trainer = FederatedTrainer(config)
        trainer.train()
        
        summary = trainer.get_summary()
        results[num_nodes] = {
            'best_accuracy': summary['best_accuracy'],
            'final_accuracy': summary['final_accuracy'],
        }
        
        print(f"Best Accuracy:  {summary['best_accuracy']:.4%}")
    
    # Compare scaling
    print("\n" + "="*70)
    print("SCALING COMPARISON")
    print("="*70)
    print(f"{'Nodes':<10} {'Best Accuracy':<20} {'Final Accuracy':<20}")
    print("-"*50)
    
    for num_nodes, metrics in results.items():
        print(
            f"{num_nodes:<10} {metrics['best_accuracy']:>18.4%} "
            f"{metrics['final_accuracy']:>18.4%}"
        )
    
    return results


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("CHAKRAVYUH - PHASE 2: FEDERATED LEARNING DEMOS")
    print("="*70)
    
    try:
        # Demo 1: Basic federated learning
        trainer1, report1 = demo_basic_federated_learning()
        
        # Demo 2: Compare strategies
        strategy_results = demo_aggregation_strategies()
        
        # Demo 3: Differential privacy
        trainer3 = demo_differential_privacy()
        
        # Demo 4: Scaling
        scaling_results = demo_scaling()
        
        print("\n" + "="*70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nGenerated files:")
        print("  - phase2_federated/demo_results/federated_training_basic.json")
        print("  - phase2_federated/demo_results/strategy_comparison.json")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
