#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Request to Plan & Todo Generator — DEMO MODE (Mock Data)

Pipeline: planning -> review -> revised planning -> todo
Uses mock data to demonstrate the orchestrator workflow

Usage:
    python request_to_plan_todo_demo.py "Your user request here"

Output:
    claude_tools/outputs/{timestamp}_plan_todo.md

NOTE: This is a demo version using simulated agent responses.
For production use, see request_to_plan_todo.py (requires Claude CLI)
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class MockOrchestrator:
    """Demo version using mock agent responses"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.output_dir = Path("claude_tools") / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_atomic(self, path, content):
        """원자적 파일 쓰기"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = f"{path}.tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp_path, path)

    def generate_plan(self, user_request: str) -> str:
        """Mock planning response"""
        return f"""## 1. Analysis
The request asks to build: "{user_request}"

Key aspects identified:
- Core system architecture required
- Component structure and relationships
- Integration points with existing systems
- Performance considerations

## 2. Approach
Strategic breakdown:
1. Define data structures (Components)
2. Create system logic (Systems)
3. Implement authoring/baker components
4. Add tests and validation

## 3. Key Components
- Core data entities (health, damage, turns)
- System logic (turn order, damage application)
- UI/Game loop integration
- Event handling and state management

## 4. Potential Issues
- Turn order synchronization across entities
- Health/damage precision in burst-compiled code
- Network synchronization (if multiplayer)
- Performance under many entities

## 5. Dependencies
- Must understand existing ECS architecture
- Requires knowledge of DOTS patterns
- Component authoring through Baker pattern
- Interaction with existing game loops"""

    def generate_review(self, user_request: str, plan: str) -> str:
        """Mock review response"""
        return f"""## Review Feedback

### Completeness: 85%
The plan covers main areas but missing:
- Specific API interfaces (IComponentData structs)
- State machine for turn progression
- Edge cases for simultaneous damage

### Clarity: 90%
Structure is clear with numbered sections. Could improve:
- More specific system names
- Example component definitions
- Concrete timing diagrams

### Feasibility: 95%
Approach is realistic and follows ECS patterns. Recommendations:
- Start with health/damage before turn management
- Use SystemAPI.Query for optimal Burst performance
- Consider struct-based systems for better performance

### Order: Good
Dependencies are in logical order:
1. Data structures first ✓
2. Systems logic second ✓
3. Integration third ✓

### Suggested Improvements
1. **Add specific component definitions**: Show IComponentData examples
2. **Include system pseudocode**: Make implementation clearer
3. **Document integration points**: How does this hook into game loop?
4. **Add performance considerations**: Burst compilation tips
5. **Include testing strategy**: How to validate turn order correctness?

## Summary
Solid foundational plan. With the suggested improvements, this will be
a comprehensive guide for implementation."""

    def generate_revised_plan(self, user_request: str, review: str) -> str:
        """Mock revised planning response"""
        return f"""# Revised Implementation Plan

## Phase 1: Core Data Structures

### Component Definitions
```
struct Health : IComponentData {{
    public int Current;
    public int Max;
}}

struct Damage : IComponentData {{
    public int Amount;
    public Entity Source;
}}

struct TurnState : IComponentData {{
    public int CurrentTurn;
    public bool IsActive;
}}
```

### Support Components
- `ActionPoints`: Tracks action economy
- `CombatantStats`: Base damage/defense
- `TurnOrder`: Global turn management

## Phase 2: Core Systems

### TakeDamageSystem
- Listens for Damage component additions
- Applies damage to Health
- Removes dead entities
- Triggers events

### TurnManagementSystem
- Cycles through active combatants
- Increments action points per turn
- Handles turn transitions
- Manages victory/defeat conditions

### HealthRegenerationSystem (Optional)
- Natural health recovery per turn
- Scales with combatant stats

## Phase 3: Authoring & Integration

### CombatantAuthoring Baker
- Converts MonoBehaviour -> ECS entities
- Sets initial health and stats
- Registers with turn manager

### GameLoopIntegration
- Connect to existing update cycle
- Handle pause/resume
- Sync with animation systems

## Phase 4: Testing & Validation

### Unit Tests
- Health calculations (edge cases)
- Turn order correctness
- State transitions
- Cleanup on entity destruction

### Integration Tests
- Multiple combatants interacting
- Turn order under load
- Memory management

## Performance Considerations
- Use Burst-compilable systems
- Avoid managed types in hot paths
- Cache EntityQueries in OnCreate
- Consider job scheduling for 100+ entities

## Timeline
- Phase 1: 2-3 hours (data structures)
- Phase 2: 4-5 hours (systems logic)
- Phase 3: 2-3 hours (integration)
- Phase 4: 3-4 hours (testing)
- **Total: 11-15 hours**"""

    def generate_todo(self, user_request: str, plan: str) -> str:
        """Mock todo generation"""
        return f"""## Combat System Implementation Checklist

### Phase 1: Data Structures (2-3 hours)

#### 1.1 Core Components
- [ ] Create Health component (Current, Max fields)
  - Acceptance: Health struct compiles and is [BurstCompile] compatible
- [ ] Create Damage component (Amount, Source fields)
  - Acceptance: Can create/add Damage to entities
- [ ] Create TurnState component (CurrentTurn, IsActive fields)
  - Acceptance: Turn tracking data accessible

#### 1.2 Support Components
- [ ] Create ActionPoints component
- [ ] Create CombatantStats component (damage/defense modifiers)
- [ ] Create TurnOrder singleton component
- [ ] Add cleanup components (DeadFlag, etc.)

### Phase 2: Core Systems (4-5 hours)

#### 2.1 TakeDamageSystem
- [ ] Create ISystem with BurstCompile
- [ ] Implement damage application logic
  - Health -= Damage.Amount
  - Clamp to 0
  - Remove Damage component
- [ ] Handle entity destruction when Health <= 0
  - Add DeadFlag component
- [ ] Unit tests
  - Normal damage
  - Overkill damage
  - Zero/negative damage handling

#### 2.2 TurnManagementSystem
- [ ] Create singleton turn tracker
- [ ] Implement turn cycle logic
  - Get next active combatant
  - Reset action points
  - Increment turn counter
- [ ] Handle turn transitions (OnTurnStart/OnTurnEnd events)
- [ ] Tests:
  - Correct turn order
  - Multiple combatants
  - Skipping dead entities

#### 2.3 HealthRegenerationSystem (Optional)
- [ ] Regenerate health per turn
- [ ] Respect max health cap
- [ ] Make configurable per combatant

### Phase 3: Authoring & Integration (2-3 hours)

#### 3.1 CombatantAuthoring
- [ ] Create MonoBehaviour baker
  - [ ] Set initial health values
  - [ ] Set combatant stats
  - [ ] Register with turn manager
  - [ ] Add to EntityManager
- [ ] Test baker with prefabs

#### 3.2 Game Loop Integration
- [ ] Hook TurnManagementSystem into main loop
- [ ] Connect health UI display
- [ ] Add damage popup/VFX triggers
- [ ] Test end-to-end combat flow

### Phase 4: Testing & Validation (3-4 hours)

#### 4.1 Unit Tests
- [ ] Health system edge cases
  - [ ] Negative health handling
  - [ ] Max health clamping
- [ ] Turn order with 1/2/10 entities
- [ ] Simultaneous damage scenarios
- [ ] Cleanup verification

#### 4.2 Integration Tests
- [ ] Full combat scenario (2 entities, 5 rounds)
- [ ] Stress test (50+ entities, damage every frame)
- [ ] Memory profiling
- [ ] No memory leaks in turn cycling

#### 4.3 Code Review
- [ ] All systems use [BurstCompile]
- [ ] No managed types in hot paths
- [ ] Follows CLAUDE.md conventions
- [ ] EntityQueries cached

### Phase 5: Polish (Optional)

- [ ] Add debug visualization
- [ ] Performance profiling
- [ ] Documentation/comments
- [ ] Example scenes

---

## Notes
- Start with Health/Damage before Turn Management
- Test each system independently
- Integrate incrementally
- Profile before optimizing"""

    def run_workflow(self, user_request: str) -> str:
        """Run demo workflow"""

        print("\n" + "="*70)
        print("[DEMO] PLAN & TODO GENERATOR (Mock Data)")
        print("="*70)
        print(f"\nUser Request:\n{user_request}\n")

        # Step 1: Planning
        print("\n>> PLANNING Agent running (demo)...")
        planning_output = self.generate_plan(user_request)
        print("[OK] Planning Agent completed")

        # Step 2: Review
        print("\n>> REVIEW Agent running (demo)...")
        review_output = self.generate_review(user_request, planning_output)
        print("[OK] Review Agent completed")

        # Step 3: Revised Planning
        print("\n>> REVISED PLANNING Agent running (demo)...")
        revised_output = self.generate_revised_plan(user_request, review_output)
        print("[OK] Revised Planning Agent completed")

        # Step 4: Todo
        print("\n>> TODO Agent running (demo)...")
        todo_output = self.generate_todo(user_request, revised_output)
        print("[OK] Todo Agent completed")

        # Assemble output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"{timestamp}_plan_todo.md"

        final_output = f"""# Plan & Todo Generation — {timestamp}

## User Request
{user_request}

---

## [PLAN] Revised Planning

{revised_output}

---

## [TODO] Todo List

{todo_output}

---

## [SUMMARY] Generation Summary
- Planning: [OK] Generated initial plan (demo mode)
- Review: [OK] Reviewed and provided feedback (demo mode)
- Revised Planning: [OK] Incorporated feedback (demo mode)
- Todo: [OK] Generated actionable tasks (demo mode)
- Generated at: {datetime.now().isoformat()}

---

## Demo Mode Notice
This output was generated using mock agent responses for demonstration.
For production use with real Claude AI agents, use `request_to_plan_todo.py`
(requires Claude CLI to be properly configured).
"""

        self.write_atomic(str(output_file), final_output)

        print("\n" + "="*70)
        print("[SUCCESS] WORKFLOW COMPLETED")
        print("="*70)
        print(f"\n[OUTPUT] Saved to: {output_file}")

        return str(output_file)


def main():
    """Main entry point"""

    if len(sys.argv) < 2:
        print("Usage: python request_to_plan_todo_demo.py '<your request>'")
        print("\nExample:")
        print("  python request_to_plan_todo_demo.py 'Create a combat system'")
        sys.exit(1)

    user_request = sys.argv[1]

    # Project root
    project_root = Path(__file__).parent.parent

    orchestrator = MockOrchestrator(str(project_root))
    result = orchestrator.run_workflow(user_request)

    if result:
        print(f"\n[OK] Output file created at:\n   {result}\n")

        # Display summary
        print("\nGenerated Files:")
        print(f"  - Plan & Todo: {result}")

        sys.exit(0)
    else:
        print("\n[ERROR] Failed to generate output.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
