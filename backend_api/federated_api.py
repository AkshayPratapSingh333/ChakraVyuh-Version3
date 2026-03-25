"""
Phase 2 Federated Learning API Endpoints
Integration with FastAPI backend for federated training
"""

from fastapi import APIRouter, HTTPException, Query, WebSocket
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import asyncio
import sys
import os
import time
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Add parent directory to path to import phase2_federated
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from phase2_federated.federated_config import FederatedConfig, AggregationStrategy
    from phase2_federated.federated_trainer import FederatedTrainer
    IMPORTS_SUCCESS = True
except ImportError as e:
    logger.error(f"Failed to import federated modules: {e}")
    IMPORTS_SUCCESS = False

# Create router
router = APIRouter(prefix="/api/v1/federated", tags=["federated"])

# Global state
federated_trainer: Optional[FederatedTrainer] = None
federated_running = False
federated_metrics_history: List[Dict[str, Any]] = []
_training_start_time: Optional[float] = None
TRAINING_TIMEOUT = 300  # 5 minutes timeout


async def run_federated_training_background(fed_config):
    """Run federated training in background."""
    global federated_trainer, federated_running, federated_metrics_history, _training_start_time
    try:
        logger.info("[BG-TRAIN] Starting background training task...")
        federated_trainer = FederatedTrainer(fed_config)
        round_metrics = federated_trainer.train()
        federated_metrics_history = round_metrics
        logger.info("[BG-TRAIN] ✓ Training completed successfully")
    except Exception as e:
        logger.error(f"[BG-TRAIN] ✗ Training failed: {type(e).__name__}: {e}", exc_info=True)
    finally:
        federated_running = False
        logger.info("[BG-TRAIN] Training task finished")


def format_metrics_for_frontend(metrics_history: List[Dict]) -> List[Dict]:
    """Convert federated trainer metrics to frontend-compatible format."""
    formatted = []
    for i, round_metrics in enumerate(metrics_history):
        # Extract node accuracies
        node_accuracies = {}
        if 'node_metrics' in round_metrics:
            for node_id, metrics in round_metrics['node_metrics'].items():
                # Convert numpy types to Python native types
                acc = metrics.get('accuracy', 0.0)
                node_accuracies[node_id] = float(acc) if hasattr(acc, 'item') else float(acc)
        
        # Convert numpy types to Python natives
        global_acc = round_metrics.get('avg_accuracy', 0.0)
        global_acc = float(global_acc) if hasattr(global_acc, 'item') else float(global_acc)
        
        avg_loss = round_metrics.get('avg_loss', 0.0)
        avg_loss = float(avg_loss) if hasattr(avg_loss, 'item') else float(avg_loss)
        
        formatted.append({
            'round': i + 1,
            'timestamp': round_metrics.get('timestamp'),
            'global_accuracy': global_acc,
            'avg_loss': avg_loss,
            'node_accuracies': node_accuracies,
            'node_metrics': round_metrics.get('node_metrics', {}),
            'aggregation_metrics': round_metrics.get('aggregation_metrics', {}),
        })
    return formatted


def reset_training_state():
    """Reset federated training state."""
    global federated_trainer, federated_running, federated_metrics_history, _training_start_time
    federated_trainer = None
    federated_running = False
    federated_metrics_history = []
    _training_start_time = None
    logger.info("[RESET] Federated training state reset")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class FederatedConfigRequest(BaseModel):
    """Request model for starting federated training."""
    num_rounds: int = 5
    num_nodes: int = 3
    local_epochs: int = 2
    learning_rate: float = 0.01
    aggregation_strategy: str = "fedavg"
    differential_privacy: bool = False
    dp_epsilon: float = 1.0
    dp_delta: float = 0.01
    clip_weights: bool = True


class FederatedStatusResponse(BaseModel):
    """Response model for federated training status."""
    running: bool
    current_round: int
    total_rounds: int
    num_nodes: int
    best_accuracy: float
    final_accuracy: float
    aggregation_strategy: str


# ============================================================================
# FEDERATED LEARNING ENDPOINTS
# ============================================================================

@router.post("/start-training")
async def start_federated_training(config: FederatedConfigRequest) -> Dict[str, Any]:
    """
    Start federated learning training (non-blocking).
    
    Args:
        config: Federated training configuration
        
    Returns:
        Training started response (returns immediately)
    """
    global federated_trainer, federated_running, federated_metrics_history, _training_start_time
    
    # Check if previous training timed out and reset
    if federated_running and _training_start_time:
        elapsed = time.time() - _training_start_time
        if elapsed > TRAINING_TIMEOUT:
            logger.warning(f"[START-TRAINING] Previous training timed out ({elapsed:.0f}s > {TRAINING_TIMEOUT}s), resetting...")
            reset_training_state()
    
    logger.info(f"[START-TRAINING] Request received: {config.dict()}")
    
    if not IMPORTS_SUCCESS:
        logger.error("[START-TRAINING] Federated modules failed to import")
        raise HTTPException(status_code=503, detail="Federated learning modules failed to import. Check backend logs for details.")
    
    if federated_running:
        logger.warning("[START-TRAINING] Training already in progress")
        raise HTTPException(status_code=400, detail="Training already in progress")
    
    try:
        # Create federated config
        logger.info(f"[START-TRAINING] Creating FederatedConfig with strategy: {config.aggregation_strategy}")
        fed_config = FederatedConfig(
            num_rounds=config.num_rounds,
            num_nodes=config.num_nodes,
            local_epochs=config.local_epochs,
            learning_rate=config.learning_rate,
            aggregation_strategy=AggregationStrategy(config.aggregation_strategy),
            differential_privacy=config.differential_privacy,
            dp_epsilon=config.dp_epsilon,
            dp_delta=config.dp_delta,
            clip_weights=config.clip_weights,
        )
        
        # Set state BEFORE starting background task
        federated_running = True
        _training_start_time = time.time()
        federated_metrics_history = []
        
        # Schedule training to run in background (non-blocking)
        logger.info("[START-TRAINING] Scheduling background training task...")
        asyncio.create_task(run_federated_training_background(fed_config))
        
        # Return immediately
        logger.info(
            f"[START-TRAINING] ✓ Training scheduled: {config.num_rounds} rounds, {config.num_nodes} nodes"
        )
        
        return {
            'status': 'scheduled',
            'message': 'Training scheduled to start in background',
            'num_rounds': config.num_rounds,
            'num_nodes': config.num_nodes,
            'aggregation_strategy': config.aggregation_strategy,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[START-TRAINING] ✗ Exception: {type(e).__name__}: {e}", exc_info=True)
        federated_running = False
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/status")
async def get_federated_status() -> Dict[str, Any]:
    """Get current federated training status with detailed metrics."""
    
    logger.info(f"[STATUS] Request received. federated_trainer={bool(federated_trainer)}, metrics_history_len={len(federated_metrics_history)}")
    
    if not federated_trainer and not federated_metrics_history:
        logger.info("[STATUS] No active training, returning idle state")
        return {
            'status': 'idle',
            'running': False,
            'current_round': 0,
            'total_rounds': 0,
            'global_accuracy': 0.0,
            'best_accuracy': 0.0,
            'final_accuracy': 0.0,
            'node_accuracies': {},
            'metrics_history': [],
        }
    
    config = federated_trainer.config if federated_trainer else None
    
    # Calculate current round based on metrics history
    current_round = len(federated_metrics_history)
    total_rounds = config.num_rounds if config else 0
    
    # Get accuracies from metrics history
    best_accuracy = max(
        [m.get('avg_accuracy', 0) for m in federated_metrics_history],
        default=0.0
    )
    final_accuracy = federated_metrics_history[-1].get('avg_accuracy', 0.0) if federated_metrics_history else 0.0
    
    # Extract node accuracies from last round
    node_accuracies = {}
    if federated_metrics_history and 'node_metrics' in federated_metrics_history[-1]:
        for node_id, metrics in federated_metrics_history[-1]['node_metrics'].items():
            node_accuracies[node_id] = metrics.get('accuracy', 0.0)
    
    formatted_metrics = format_metrics_for_frontend(federated_metrics_history)
    logger.info(f"[STATUS] Returning: rounds={current_round}, total={total_rounds}, accuracy={float(final_accuracy):.4f}, nodes={len(node_accuracies)}")
    logger.info(f"[STATUS] Formatted metrics: {len(formatted_metrics)} rounds")
    
    return {
        'status': 'training' if federated_running else 'completed',
        'running': federated_running,
        'current_round': current_round,
        'total_rounds': total_rounds,
        'num_nodes': config.num_nodes if config else 0,
        'num_nodes_registered': len(federated_trainer.nodes) if federated_trainer else 0,
        'global_accuracy': float(final_accuracy),  # Frontend expects this field name
        'best_accuracy': float(best_accuracy),
        'final_accuracy': float(final_accuracy),
        'node_accuracies': node_accuracies,
        'aggregation_strategy': config.aggregation_strategy.value if config else 'fedavg',
        'differential_privacy': config.differential_privacy if config else False,
        'metrics_history': formatted_metrics,  # Return formatted
    }



@router.get("/summary")
async def get_federated_summary() -> Dict[str, Any]:
    """Get federated training summary."""
    
    if not federated_trainer:
        raise HTTPException(status_code=400, detail="No training has been performed")
    
    summary = federated_trainer.get_summary()
    
    return {
        **summary,
        'rounds_metrics': federated_metrics_history,
    }


@router.get("/round-metrics/{round_num}")
async def get_round_metrics(round_num: int) -> Dict[str, Any]:
    """Get metrics for a specific round."""
    
    if round_num < 1 or round_num > len(federated_metrics_history):
        raise HTTPException(
            status_code=404,
            detail=f"Round {round_num} not found"
        )
    
    return federated_metrics_history[round_num - 1]


@router.get("/metrics")
async def get_all_metrics() -> List[Dict[str, Any]]:
    """Get all round metrics."""
    return format_metrics_for_frontend(federated_metrics_history)


@router.post("/run-demo")
async def run_federated_demo(
    num_rounds: int = Query(3, ge=1, le=10),
    num_nodes: int = Query(3, ge=2, le=20),
) -> Dict[str, Any]:
    """
    Run a quick federated learning demo.
    
    Args:
        num_rounds: Number of training rounds
        num_nodes: Number of nodes
        
    Returns:
        Training results
    """
    global federated_trainer, federated_running, federated_metrics_history, _training_start_time
    
    # Check if previous training timed out and reset
    if federated_running and _training_start_time:
        elapsed = time.time() - _training_start_time
        if elapsed > TRAINING_TIMEOUT:
            logger.warning(f"[RUN-DEMO] Previous training timed out ({elapsed:.0f}s > {TRAINING_TIMEOUT}s), resetting...")
            reset_training_state()
    
    logger.info(f"[RUN-DEMO] Request received: rounds={num_rounds}, nodes={num_nodes}")
    
    if not IMPORTS_SUCCESS:
        logger.error("[RUN-DEMO] Federated modules not available")
        raise HTTPException(status_code=503, detail="Federated learning modules failed to import. Check backend logs for details.")
    
    if federated_running:
        logger.warning("[RUN-DEMO] Training already in progress")
        raise HTTPException(status_code=400, detail="Training already in progress")
    
    try:
        logger.info("[RUN-DEMO] ✓ Starting demo training...")
        federated_running = True
        _training_start_time = time.time()
        federated_metrics_history = []
        
        # Create config
        logger.info(f"[RUN-DEMO] Creating FederatedConfig...")
        config = FederatedConfig(
            num_rounds=num_rounds,
            num_nodes=num_nodes,
            local_epochs=1,
        )
        
        # Train
        logger.info("[RUN-DEMO] Initializing trainer and starting training...")
        federated_trainer = FederatedTrainer(config)
        round_metrics = federated_trainer.train()
        
        # Store metrics
        federated_metrics_history = round_metrics
        logger.info(f"[RUN-DEMO] Metrics stored: {len(federated_metrics_history)} rounds")
        if federated_metrics_history:
            logger.info(f"[RUN-DEMO] First round metrics: {federated_metrics_history[0]}")
            logger.info(f"[RUN-DEMO] Last round metrics: {federated_metrics_history[-1]}")
        
        # Get summary
        logger.info("[RUN-DEMO] Getting training summary...")
        summary = federated_trainer.get_summary()
        logger.info(f"[RUN-DEMO] Summary: {summary}")
        
        federated_running = False
        logger.info("[RUN-DEMO] ✓ Demo completed successfully")
        
        return {
            'status': 'completed',
            'summary': summary,
            'num_rounds': num_rounds,
            'num_nodes': num_nodes,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        federated_running = False
        logger.error(f"[RUN-DEMO] ✗ Exception: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")


@router.post("/stop-training")
async def stop_federated_training() -> Dict[str, str]:
    """Stop federated training."""
    global federated_running
    
    if not federated_running:
        raise HTTPException(status_code=400, detail="No training in progress")
    
    federated_running = False
    
    return {'status': 'stopped'}


@router.post("/reset")
async def reset_federated_state() -> Dict[str, str]:
    """Reset federated training state (useful for debugging/testing)."""
    logger.info("[RESET] Manual reset requested")
    reset_training_state()
    return {'status': 'reset', 'message': 'Federated training state has been reset'}


@router.get("/node-stats")
async def get_node_statistics() -> Dict[str, Any]:
    """Get statistics for all nodes."""
    
    if not federated_trainer:
        raise HTTPException(status_code=400, detail="No training active")
    
    node_stats = {}
    for node_id, node in federated_trainer.nodes.items():
        node_stats[node_id] = node.get_statistics()
    
    return {'nodes': node_stats}


@router.get("/server-stats")
async def get_server_statistics() -> Dict[str, Any]:
    """Get aggregation server statistics."""
    
    if not federated_trainer:
        raise HTTPException(status_code=400, detail="No training active")
    
    return federated_trainer.server.get_statistics()


# ============================================================================
# WEBSOCKET SUPPORT (for real-time updates)
# ============================================================================

federated_ws_clients: set = set()


async def broadcast_federated_update(update: Dict[str, Any]):
    """Broadcast federated training update to all WebSocket clients."""
    message = json.dumps({
        'type': 'federated_update',
        **update
    })
    
    disconnected = set()
    for client in federated_ws_clients:
        try:
            await client.send_text(message)
        except:
            disconnected.add(client)
    
    # Clean up disconnected clients
    federated_ws_clients.difference_update(disconnected)


@router.websocket("/ws/training")
async def websocket_federated_training(websocket: WebSocket):
    """WebSocket endpoint for real-time federated training updates."""
    await websocket.accept()
    federated_ws_clients.add(websocket)
    
    try:
        # Send current status
        status = await get_federated_status()
        await websocket.send_json({
            'type': 'status',
            **status
        })
        
        # Keep connection alive and listen for messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Handle incoming messages if needed
                message = json.loads(data)
                logger.debug(f"Received message: {message}")
            except asyncio.TimeoutError:
                # Send periodic status update
                if federated_trainer:
                    status = await get_federated_status()
                    await websocket.send_json({
                        'type': 'status',
                        **status
                    })
            except Exception as e:
                logger.debug(f"WebSocket error: {e}")
                break
    
    finally:
        federated_ws_clients.discard(websocket)
