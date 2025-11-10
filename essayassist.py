import os
from dotenv import load_dotenv

import openai
from openai import APIError

# Load environment variables
load_dotenv()

# Check if API key is available (dynamic check)
def is_api_key_available():
    return bool(os.environ.get('OPENAI_API_KEY'))

def demo_analyze_response(essay_text):
    """Demo response for essay analysis when no API key is available"""
    demo_response = f"""# Essay Analysis

## **Narrative and Storytelling**: 75/100
Your essay shows a clear narrative structure, but could benefit from more vivid imagery and emotional depth.

## **Personal Reflection and Growth**: 68/100
Good reflection on experiences, though deeper introspection would strengthen this aspect.

## **Unique Voice and Authenticity**: 72/100
Your voice comes through, but consider making it more distinctive and personal.

## **Clear Structure and Logical Flow**: 80/100
Well-organized with logical progression between ideas.

## **Connection to Larger Themes or Ideas**: 65/100
Some connections made, but could explore broader implications more deeply.

## **Intellectual Curiosity**: 70/100
Shows interest in learning, though could demonstrate more academic passion.

## **Impact and Initiative**: 73/100
Good examples of taking action, but could highlight leadership more.

## **Diversity and Global Perspective**: 60/100
Limited global perspective - consider expanding your worldview.

## **Readability and Flow**: 78/100
Generally readable, though some sentences could be more concise.

## **Uniqueness**: 70/100
Your story has unique elements, but could be more distinctive.

## **Overall Score: 71/100**

**Key Areas for Improvement:**
- Add more specific, vivid details
- Deepen personal reflection
- Expand global perspective
- Make your voice more distinctive

*Note: This is a demo response. Add your OpenAI API key for real AI-powered analysis.*"""
    
    def stream():
        for line in demo_response.split('\n'):
            yield line + '\n'
            import time
            time.sleep(0.05)  # Small delay for realistic streaming effect
    
    return stream()

def demo_generate_response(outline):
    """Demo response for essay generation when no API key is available"""
    demo_response = f"""# Generated Essay

Based on your outline: "{outline}"

**The Journey of Discovery**

I never imagined that a simple curiosity about how things work would lead me down such an unexpected path. It all began in my grandmother's kitchen, where I spent countless hours watching her transform simple ingredients into magical creations. Her hands moved with practiced precision, each movement telling a story of tradition and love passed down through generations.

As I grew older, my curiosity expanded beyond the kitchen. I found myself dismantling old electronics, not to break them, but to understand their inner workings. Each circuit board became a puzzle waiting to be solved, each component a piece of a larger story about human innovation and creativity.

This passion for understanding led me to volunteer at our local science museum, where I discovered the joy of sharing knowledge with others. Watching a child's eyes light up when they finally understand a complex concept reminded me of my own moments of discovery. It was here that I realized my calling: to become a bridge between complex ideas and curious minds.

The challenges I've faced have only strengthened my resolve. When our school's robotics club faced budget cuts, I didn't give up. Instead, I organized fundraisers, wrote grant proposals, and even taught myself basic programming to keep the club running. This experience taught me that passion, combined with persistence, can overcome seemingly insurmountable obstacles.

Looking toward the future, I see myself not just as a student of science, but as a storyteller who makes complex concepts accessible to everyone. Whether through teaching, research, or innovation, I want to inspire the same sense of wonder in others that has driven my own journey.

My grandmother's kitchen taught me that the best creations come from combining tradition with innovation, patience with passion. As I move forward in my academic journey, I carry these lessons with me, ready to discover new ways to connect, create, and inspire.

*Note: This is a demo response. Add your OpenAI API key for real AI-powered essay generation.*"""
    
    def stream():
        for line in demo_response.split('\n'):
            yield line + '\n'
            import time
            time.sleep(0.05)  # Small delay for realistic streaming effect
    
    return stream()


def generate_response(messages, model_type, max_tokens):
    def stream():
        try:
            # Create client instance for this function
            openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
            response = openai_client.chat.completions.create(
                model=model_type, messages=messages, max_tokens=max_tokens, stream=True
            )

            for chunk in response:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    content = delta.content if delta.content else ''
                    if content:
                        yield content

        except Exception as exp:
            print("Error:", exp)
            yield f"Error occurred: {str(exp)}"

    return stream()


def analyze_essay(essay_text):
    # If no API key, return demo response
    if not is_api_key_available():
        return demo_analyze_response(essay_text)
    
    # Check if API key is valid by testing it first
    try:
        test_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        test_client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': 'test'}],
            max_tokens=1
        )
    except Exception as e:
        if "invalid_api_key" in str(e) or "Incorrect API key" in str(e):
            print("⚠️ Invalid API key detected, using demo response")
            return demo_analyze_response(essay_text)
        else:
            print(f"⚠️ API error: {e}, using demo response")
            return demo_analyze_response(essay_text)
    
    request_data = {
        "role": "user",
        "content": f"""
Analyze college essays.

Here is the essay: {essay_text}
""",
    }
    try:
        response = generate_response(
            model_type="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """

You are an expert college admissions essay evaluator. Analyze essays using these 10 specific, measurable categories. Score each category 1-100 based on these exact criteria:

**Narrative and Storytelling (100 points)**
- 90-100: Compelling story with clear beginning, middle, end; vivid sensory details; emotional resonance
- 80-89: Good story structure with some vivid details; minor gaps in narrative flow
- 70-79: Basic story present but lacks depth or vivid details; some structural issues
- 60-69: Weak narrative; minimal storytelling elements; poor structure
- Below 60: No clear story or narrative; confusing or absent structure

**Personal Reflection and Growth (100 points)**
- 90-100: Deep, mature reflection; clear personal growth demonstrated; sophisticated self-awareness
- 80-89: Good reflection with clear growth; some depth in self-analysis
- 70-79: Basic reflection present; limited depth in personal analysis
- 60-69: Superficial reflection; minimal personal growth shown
- Below 60: No meaningful reflection or personal growth demonstrated

**Unique Voice and Authenticity (100 points)**
- 90-100: Distinctive, authentic voice; original perspective; genuine personality shines through
- 80-89: Clear personal voice; mostly authentic; some originality
- 70-79: Generic voice; limited authenticity; few original insights
- 60-69: Weak or absent voice; sounds formulaic; lacks personality
- Below 60: No distinctive voice; completely generic or inauthentic

**Clear Structure and Logical Flow (100 points)**
- 90-100: Perfect logical progression; smooth transitions; clear organization
- 80-89: Good structure with minor flow issues; mostly logical progression
- 70-79: Basic structure but some logical gaps; awkward transitions
- 60-69: Poor organization; confusing flow; major structural issues
- Below 60: No clear structure; illogical progression; incoherent

**Connection to Larger Themes or Ideas (100 points)**
- 90-100: Sophisticated connections to broader themes; deep intellectual engagement
- 80-89: Good connections to larger ideas; some depth in thematic exploration
- 70-79: Basic connections present; limited thematic depth
- 60-69: Weak or superficial connections; minimal thematic exploration
- Below 60: No meaningful connections to larger themes or ideas

**Intellectual Curiosity (100 points)**
- 90-100: Exceptional intellectual engagement; sophisticated thinking; deep curiosity demonstrated
- 80-89: Strong intellectual curiosity; good engagement with ideas
- 70-79: Basic intellectual engagement; limited curiosity shown
- 60-69: Minimal intellectual curiosity; superficial engagement
- Below 60: No evidence of intellectual curiosity or engagement

**Impact and Initiative (100 points)**
- 90-100: Significant impact demonstrated; clear leadership; substantial initiative taken
- 80-89: Good impact and initiative; some leadership demonstrated
- 70-79: Basic impact shown; limited initiative or leadership
- 60-69: Minimal impact; weak initiative; no leadership shown
- Below 60: No evidence of impact, initiative, or leadership

**Diversity and Global Perspective (100 points)**
- 90-100: Sophisticated global awareness; deep cultural understanding; broad perspective
- 80-89: Good global perspective; some cultural awareness
- 70-79: Basic global awareness; limited cultural perspective
- 60-69: Minimal global perspective; narrow worldview
- Below 60: No evidence of global awareness or cultural understanding

**Readability and Flow (100 points)**
- 90-100: Exceptional writing; perfect flow; sophisticated language; no clichés
- 80-89: Good writing with minor issues; mostly smooth flow; few clichés
- 70-79: Basic writing quality; some flow issues; some clichés present
- 60-69: Poor writing quality; awkward flow; many clichés
- Below 60: Very poor writing; choppy flow; excessive clichés and cringe

**Uniqueness (100 points)**
- 90-100: Highly unique and distinctive; stands out significantly; original approach
- 80-89: Good uniqueness; some distinctive elements; mostly original
- 70-79: Basic uniqueness; limited distinctive elements; some originality
- 60-69: Minimal uniqueness; generic elements; limited originality
- Below 60: No uniqueness; completely generic; no originality

SCORING RULES:
1. Be consistent and objective in your scoring
2. Deduct points for clichés, generic language, and cringe-worthy content
3. Reward specificity, authenticity, and originality
4. Provide specific examples of what earned or lost points
5. Calculate overall score as the average of all 10 categories
6. Use markdown formatting with bolded section titles

Format your response with each category as a section, followed by the overall score.
""",
                },
                request_data,
            ],
            max_tokens=5000,
        )

        return response
    except Exception as e:
        return str(e)


def rewrite_essay(essay_text):
    """Rewrite an essay to make it better using OpenAI"""
    # If no API key, return demo response
    if not is_api_key_available():
        def demo_stream():
            demo_text = "This is a demo rewrite. Add your OpenAI API key for real AI-powered essay rewriting."
            for word in demo_text.split():
                yield word + " "
                import time
                time.sleep(0.05)
        return demo_stream()
    
    # Check if API key is valid by testing it first
    try:
        test_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        test_client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': 'test'}],
            max_tokens=1
        )
    except Exception as e:
        if "invalid_api_key" in str(e) or "Incorrect API key" in str(e):
            print("⚠️ Invalid API key detected, using demo response")
            def demo_stream():
                demo_text = "This is a demo rewrite. Add your OpenAI API key for real AI-powered essay rewriting."
                for word in demo_text.split():
                    yield word + " "
                    import time
                    time.sleep(0.05)
            return demo_stream()
        else:
            print(f"⚠️ API error: {e}, using demo response")
            def demo_stream():
                demo_text = "This is a demo rewrite. Add your OpenAI API key for real AI-powered essay rewriting."
                for word in demo_text.split():
                    yield word + " "
                    import time
                    time.sleep(0.05)
            return demo_stream()
    
    request_data = {
        "role": "user",
        "content": f"""
Rewrite this college essay to make it significantly better while preserving the core message and personal voice. 

Here is the original essay:
{essay_text}

IMPORTANT INSTRUCTIONS:
1. Maintain the author's authentic voice and personal experiences - do not change the fundamental story
2. Improve clarity, flow, and impact while keeping the same length (approximately the same word count)
3. Enhance vivid details, emotional depth, and specific examples where appropriate
4. Strengthen transitions between paragraphs
5. Remove clichés and generic language, replace with more specific and authentic expressions
6. Improve sentence variety and structure for better readability
7. Deepen personal reflection and show growth more clearly
8. Make connections to larger themes more explicit
9. Ensure the essay maintains its unique perspective and doesn't sound generic
10. Keep the same first-person perspective and narrative structure
11. Do NOT add a title or any meta-commentary - just output the rewritten essay

Output ONLY the rewritten essay, nothing else. Do not include explanations, notes, or markdown formatting.
""",
    }
    try:
        response = generate_response(
            model_type="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert college essay editor with deep knowledge of what makes essays compelling for top universities. You rewrite essays to improve them while preserving the author's authentic voice and core message. You focus on enhancing clarity, specificity, emotional depth, and impact without changing the fundamental story or making it sound generic."""
                },
                request_data,
            ],
            max_tokens=4000,
        )
        return response
    except Exception as e:
        print(f"Error in rewrite_essay: {e}")
        def error_stream():
            yield f"Error occurred while rewriting: {str(e)}"
        return error_stream()


def generate_essay(outline):
    # If no API key, return demo response
    if not is_api_key_available():
        return demo_generate_response(outline)
    
    request_data = {
        "role": "user",
        "content": f"""
Craft college essays to maximize students' admission chances to top universities.
These categories are the most important for top university essays: Narrative and Storytelling, Personal Reflection and Growth, Unique Voice and Authenticity, Clear Structure and Logical Flow, Connection to Larger Themes or Ideas, Intellectual Curiosity, Impact and Initiative, Diversity and Global Perspective, Readability and Flow, and Uniqueness
ONLY output a full essay draft between 450-500 words, NOT an outline. Absolutely no more than 550 words. OUTPUT NOTHING BUT THE DRAFTED ESSAY. avoid cliches and cringe, while emphasizing personal growth uniqueness, and academic curiosity. try not to sound llike an LLM.
WRITE IN FIRST PERSON AND DON'T MENTION THE PERSON'S NAME.


use markdown to format the essay: all titles should be the same size as other text, but bolded.

Base the essay on this student's given information or essay outline: {outline}
""",
    }
    try:
        # response = openai.ChatCompletion.create(
        response = generate_response(
            model_type="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                request_data,
            ],
            max_tokens=7500,
        )
        # save_to_firestore(
        #     user_id, request_data, response["choices"][0]["message"]["content"].strip()
        # )
        # return response["choices"][0]["message"]["content"].strip()

        return response
    except Exception as e:
        return str(e)


