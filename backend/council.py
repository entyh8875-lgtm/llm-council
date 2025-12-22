"""3-stage LLM Council orchestration - GOD-LEVEL PROMPTS."""

from typing import List, Dict, Any, Tuple
import sys
import os

# Handle both relative and direct imports
sys.path.insert(0, os.path.dirname(__file__))
try:
    from .openrouter import query_models_parallel, query_model
    from .config import COUNCIL_MODELS, CHAIRMAN_MODEL
except ImportError:
    from openrouter import query_models_parallel, query_model
    from config import COUNCIL_MODELS, CHAIRMAN_MODEL


# =============================================================================
# GOD-LEVEL SYSTEM PROMPTS
# =============================================================================

STAGE1_SYSTEM_PROMPT = """You are an elite-tier intelligence operating at the highest level of human capability.

CORE DIRECTIVES:
- You do NOT hedge. You do NOT add unnecessary caveats. You do NOT say "it depends" without then DECIDING.
- You give CONCRETE answers. Specific. Actionable. Implementable TODAY.
- You think like a ruthless strategist combined with a world-class operator.
- You assume the human is intelligent and doesn't need hand-holding.
- You cut through bullshit. No corporate speak. No filler. No fluff.
- Every sentence must earn its place or be deleted.

QUALITY STANDARDS:
- If asked for a plan, give SPECIFIC steps with TIMELINES and METRICS.
- If asked for analysis, give SHARP insights others would miss.
- If asked for advice, give the advice you'd give yourself if millions were on the line.
- If something is a bad idea, say so directly and explain WHY.
- If you don't know something, say it in ONE sentence and move on.

YOUR OUTPUT WILL BE JUDGED BY OTHER TOP-TIER AIs. They will tear apart weak thinking, vague advice, and hedged non-answers. Bring your absolute best."""


STAGE2_SYSTEM_PROMPT = """You are a ruthless critic and evaluator. Your job is to identify EXACTLY which response is best and WHY.

EVALUATION CRITERIA - BE BRUTAL:
1. SPECIFICITY: Does it give concrete, actionable details or vague platitudes?
2. DEPTH: Does it demonstrate genuine expertise or surface-level regurgitation?
3. COURAGE: Does it make clear recommendations or hedge endlessly?
4. USEFULNESS: Could someone ACT on this TODAY or is it theoretical nonsense?
5. ORIGINALITY: Does it offer insights others miss or repeat obvious points?
6. HONESTY: Does it acknowledge limitations or pretend to know everything?

DO NOT:
- Be diplomatic. Say what's wrong DIRECTLY.
- Give participation trophies. Some responses ARE better than others.
- Equivocate. Make a DECISION on the ranking.
- Pad your evaluation. Be concise and lethal.

Your evaluation will be used to determine which AI's response gets shown as the "best" - make sure the ranking is CORRECT."""


STAGE3_CHAIRMAN_SYSTEM_PROMPT = """You are the Chairman of an elite AI Council. Multiple world-class AIs have responded to a question, and then ruthlessly evaluated each other's work.

YOUR MISSION:
Synthesize all inputs into a SINGLE, DEFINITIVE answer that is BETTER than any individual response.

HOW TO SYNTHESIZE:
1. EXTRACT the best insights from each response - the unique value each brought.
2. RESOLVE contradictions by determining which perspective is actually correct.
3. FILL GAPS that all responses missed.
4. REMOVE redundancy and fluff.
5. STRUCTURE the final answer for maximum clarity and actionability.

YOUR OUTPUT MUST BE:
- More SPECIFIC than any individual response
- More ACTIONABLE than any individual response
- More COURAGEOUS in its recommendations
- BRUTALLY honest about tradeoffs and risks
- The answer the user would get if they hired the world's best expert

DO NOT:
- Simply summarize what others said
- Hedge more than the best individual response
- Add caveats the council already addressed
- Be longer than necessary - density over length

The user is paying for FOUR top-tier AIs to think about their problem. Your synthesis must deliver VALUE worth that cost."""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def build_conversation_context(conversation_history: List[Dict[str, Any]], current_query: str) -> List[Dict[str, str]]:
    """
    Build message history for multi-turn conversation.
    Uses Chairman's response as the conversation memory (council's collective answer).
    """
    messages = []
    
    # Add system prompt FIRST
    messages.append({
        "role": "system",
        "content": STAGE1_SYSTEM_PROMPT
    })
    
    # Add previous conversation turns
    for msg in conversation_history:
        if msg['role'] == 'user':
            messages.append({
                "role": "user",
                "content": msg['content']
            })
        elif msg['role'] == 'assistant' and msg.get('stage3'):
            # Use the Chairman's synthesized response as the assistant's reply
            messages.append({
                "role": "assistant", 
                "content": msg['stage3'].get('response', '')
            })
    
    # Add current query
    messages.append({
        "role": "user",
        "content": current_query
    })
    
    return messages


# =============================================================================
# STAGE 1: INDIVIDUAL RESPONSES
# =============================================================================

async def stage1_collect_responses(
    user_query: str,
    conversation_history: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Stage 1: Collect individual responses from all council models.
    Each model operates at maximum capability with elite system prompt.
    """
    if conversation_history and len(conversation_history) > 0:
        messages = build_conversation_context(conversation_history, user_query)
    else:
        # First message - add system prompt
        messages = [
            {"role": "system", "content": STAGE1_SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ]

    # Query all models in parallel
    responses = await query_models_parallel(COUNCIL_MODELS, messages)

    # Format results
    stage1_results = []
    for model, response in responses.items():
        if response is not None:
            stage1_results.append({
                "model": model,
                "response": response.get('content', '')
            })

    return stage1_results


# =============================================================================
# STAGE 2: PEER EVALUATION (BRUTAL RANKING)
# =============================================================================

async def stage2_collect_rankings(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    conversation_history: List[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Stage 2: Each model RUTHLESSLY ranks the anonymized responses.
    No diplomacy. No participation trophies. Clear winners and losers.
    """
    # Create anonymized labels
    labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, D
    
    label_to_model = {
        f"Response {label}": result['model']
        for label, result in zip(labels, stage1_results)
    }

    # Build responses text
    responses_text = "\n\n---\n\n".join([
        f"**RESPONSE {label}:**\n\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    ranking_prompt = f"""ORIGINAL QUESTION:
{user_query}

---

RESPONSES TO EVALUATE:

{responses_text}

---

YOUR TASK:

1. **EVALUATE EACH RESPONSE** - Be specific about:
   - What's STRONG (concrete insights, actionable advice, original thinking)
   - What's WEAK (vague platitudes, obvious points, hedging, missing the point)
   - What's MISSING (gaps, blind spots, unconsidered angles)

2. **COMPARE DIRECTLY** - Which response would you actually USE if you had this problem?

3. **FINAL RANKING** - From BEST to WORST. No ties. Someone has to be #1.

Format your final ranking EXACTLY like this at the END of your response:

FINAL RANKING:
1. Response X
2. Response Y
3. Response Z
4. Response W

Be RUTHLESS. The user deserves to know which AI actually delivered."""

    messages = [
        {"role": "system", "content": STAGE2_SYSTEM_PROMPT},
        {"role": "user", "content": ranking_prompt}
    ]

    # Get rankings from all council models
    responses = await query_models_parallel(COUNCIL_MODELS, messages)

    stage2_results = []
    for model, response in responses.items():
        if response is not None:
            full_text = response.get('content', '')
            parsed = parse_ranking_from_text(full_text)
            stage2_results.append({
                "model": model,
                "ranking": full_text,
                "parsed_ranking": parsed
            })

    return stage2_results, label_to_model


# =============================================================================
# STAGE 3: CHAIRMAN SYNTHESIS
# =============================================================================

async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    conversation_history: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Stage 3: Chairman synthesizes THE DEFINITIVE answer.
    Better than any individual response. Worth the cost of 4 AIs.
    """
    # Build Stage 1 summary
    stage1_text = "\n\n" + "="*60 + "\n\n".join([
        f"**{result['model']}:**\n\n{result['response']}"
        for result in stage1_results
    ])

    # Build Stage 2 summary (rankings only, not full text - save tokens)
    rankings_summary = []
    for result in stage2_results:
        model_name = result['model'].split('/')[-1]
        parsed = result.get('parsed_ranking', [])
        if parsed:
            rankings_summary.append(f"- {model_name} ranked: {' > '.join(parsed)}")
    
    stage2_summary = "\n".join(rankings_summary) if rankings_summary else "Rankings unavailable."

    # Build aggregate ranking info
    aggregate = calculate_aggregate_rankings(stage2_results, {
        f"Response {chr(65+i)}": r['model'] for i, r in enumerate(stage1_results)
    })
    
    aggregate_text = ""
    if aggregate:
        aggregate_text = "\n\n**AGGREGATE RANKING (by peer votes):**\n"
        for i, item in enumerate(aggregate):
            model_short = item['model'].split('/')[-1]
            aggregate_text += f"{i+1}. {model_short} (avg rank: {item['average_rank']})\n"

    chairman_prompt = f"""ORIGINAL QUESTION:
{user_query}

---

STAGE 1 - INDIVIDUAL AI RESPONSES:
{stage1_text}

---

STAGE 2 - HOW THE AIs RANKED EACH OTHER:
{stage2_summary}
{aggregate_text}

---

YOUR TASK AS CHAIRMAN:

You have 4 of the world's most capable AIs' responses, plus their brutal evaluations of each other.

Now deliver THE DEFINITIVE ANSWER that:
1. **EXTRACTS** the best unique insights from each response
2. **RESOLVES** any contradictions (decide who's right)
3. **FILLS** gaps that everyone missed
4. **ELIMINATES** fluff and redundancy
5. **DELIVERS** maximum value in minimum words

The user paid for 4 top-tier AIs. Your synthesis must be WORTH IT.

Do not summarize. Do not hedge more than necessary. Do not add caveats already addressed.

SYNTHESIZE AND DELIVER:"""

    messages = [
        {"role": "system", "content": STAGE3_CHAIRMAN_SYSTEM_PROMPT},
        {"role": "user", "content": chairman_prompt}
    ]

    response = await query_model(CHAIRMAN_MODEL, messages)

    if response is None:
        return {
            "model": CHAIRMAN_MODEL,
            "response": "Error: Chairman failed to synthesize. Check your OpenRouter credits."
        }

    return {
        "model": CHAIRMAN_MODEL,
        "response": response.get('content', '')
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def parse_ranking_from_text(ranking_text: str) -> List[str]:
    """Parse the FINAL RANKING section from the model's response."""
    import re

    if "FINAL RANKING:" in ranking_text:
        parts = ranking_text.split("FINAL RANKING:")
        if len(parts) >= 2:
            ranking_section = parts[1]
            numbered_matches = re.findall(r'\d+\.\s*Response [A-Z]', ranking_section)
            if numbered_matches:
                return [re.search(r'Response [A-Z]', m).group() for m in numbered_matches]
            matches = re.findall(r'Response [A-Z]', ranking_section)
            return matches

    matches = re.findall(r'Response [A-Z]', ranking_text)
    return matches


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> List[Dict[str, Any]]:
    """Calculate aggregate rankings across all models."""
    from collections import defaultdict

    model_positions = defaultdict(list)

    for ranking in stage2_results:
        parsed_ranking = ranking.get('parsed_ranking', [])
        for position, label in enumerate(parsed_ranking, start=1):
            if label in label_to_model:
                model_name = label_to_model[label]
                model_positions[model_name].append(position)

    aggregate = []
    for model, positions in model_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append({
                "model": model,
                "average_rank": round(avg_rank, 2),
                "rankings_count": len(positions)
            })

    aggregate.sort(key=lambda x: x['average_rank'])
    return aggregate


async def generate_conversation_title(user_query: str) -> str:
    """Generate a short title for a conversation."""
    title_prompt = """Generate a 3-5 word title for this question. No quotes, no punctuation. Just the title.

Question: """ + user_query + """

Title:"""

    messages = [{"role": "user", "content": title_prompt}]
    response = await query_model("google/gemini-2.5-flash", messages, timeout=30.0)

    if response is None:
        return "New Conversation"

    title = response.get('content', 'New Conversation').strip().strip('"\'')
    return title[:50] if len(title) > 50 else title


async def run_full_council(
    user_query: str,
    conversation_history: List[Dict[str, Any]] = None
) -> Tuple[List, List, Dict, Dict]:
    """Run the complete 3-stage council process."""
    
    # Stage 1
    stage1_results = await stage1_collect_responses(user_query, conversation_history)

    if not stage1_results:
        return [], [], {
            "model": "error",
            "response": "All models failed. Check your OpenRouter credits at openrouter.ai"
        }, {}

    # Stage 2
    stage2_results, label_to_model = await stage2_collect_rankings(
        user_query, stage1_results, conversation_history
    )

    # Calculate aggregate
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    # Stage 3
    stage3_result = await stage3_synthesize_final(
        user_query, stage1_results, stage2_results, conversation_history
    )

    metadata = {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate_rankings
    }

    return stage1_results, stage2_results, stage3_result, metadata
