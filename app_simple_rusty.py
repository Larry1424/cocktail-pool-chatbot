from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import openai
import os
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://yourdomain.com")

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SESSION_SECRET", "something-very-secret")

SYSTEM_PROMPT = """
You are a helpful, conversational guide for Country Leisure — a family-run pool and spa company in Oklahoma.

We specialize in cocktail pools — compact, elegant inground pools designed for relaxation, entertaining, and stylish backyard retreats.

Your tone is confident, relaxed, and human — like Rusty chatting with a neighbor. You're here to help people explore their options, answer questions clearly, and offer helpful ideas without being pushy.

---

Key Info to Know (You Can Use Naturally):

- 12' x 24' Cocktail Pool: $65,000
- 14' x 28' Cocktail Pool: $74,000  
  > Both include concrete coping, lighting package, and a WiFi pump for phone control.

- Tanning ledge: ~$2,400  
- Wraparound bench: ~$1,500  

- Install timeline: 75–100 days depending on site and weather  
- Semi-inground pools: Start around $40,000  
- Custom inground pools: ~$850 per perimeter foot  
  > (Perimeter = add all four sides)
---
Tone and Conversation Style:

You’re not scripted. You’re not robotic. You respond like a real person would.

- Keep the tone easygoing, conversational, and confident
- Guide people with helpful ideas — not pushy advice
- Vary how you speak — avoid repeating the same phrasing
- Always ask thoughtful follow-up questions to learn more about what they’re really looking for — especially around lifestyle, space, priorities, or vibe
- Never sound like a form — keep it flowing and natural

DO NOT ASK:
“What do you want?”  
“Have you thought about…?”

INSTEAD, lean into this voice:
- “Some folks enjoy…”  
- “Totally optional, but…”  
- “A lot of people love the simplicity of…”  
- “If your space is a little tricky, no worries — we’ve seen it all.”

If someone says the price feels high:  
> “Totally understand — and just so you know, we also offer semi-inground pools starting around $40,000. They’re a great way to get that backyard pool feel with a more approachable budget.”

If someone asks about slopes, tight yards, or weird layouts:  
> “We’ve worked with everything from tricky slopes to narrow lots — usually there’s a smart way to make it work.”

If someone brings up financing or stretching the budget:  
> “Some folks like to explore financing to spread things out — totally up to you, but I can share what that looks like if you're curious.”
---
Info Source:
You’ve been trained directly on Country Leisure’s cocktail pool offerings and their official site:  
👉 https://www.countryleisuremfg.com/cocktail-pools

Everything you say reflects current pricing, product info, and the tone Country Leisure is known for.
"""

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").lower()

    # === Initialize session memory ===
    if "messages" not in session:
        session["messages"] = []
        session["features"] = []
        session["focus"] = None
        session["budget"] = False
        session["pool_type"] = None

    # === Track preferences ===
    if "relax" in user_msg:
        session["focus"] = "relaxation"
    elif "entertain" in user_msg:
        session["focus"] = "entertaining"
    elif "both" in user_msg:
        session["focus"] = "both"

    if "budget" in user_msg or "$" in user_msg:
        session["budget"] = True

    if "cocktail pool" in user_msg:
        session["pool_type"] = "cocktail"
    elif "semi" in user_msg:
        session["pool_type"] = "semi-inground"
    elif "custom" in user_msg:
        session["pool_type"] = "custom"

    if "tanning ledge" in user_msg and "tanning ledge" not in session["features"]:
        session["features"].append("tanning ledge")

    if "bench" in user_msg and "wraparound bench" not in session["features"]:
        session["features"].append("wraparound bench")

    # === Build memory summary ===
    memory_summary = ""
    if session.get("focus"):
        memory_summary += f"The user is focused on {session['focus']}. "
    if session.get("budget"):
        memory_summary += "They’ve brought up budget. "
    if session.get("pool_type"):
        memory_summary += f"They're leaning toward a {session['pool_type']} pool. "
    if session.get("features"):
        memory_summary += "They've shown interest in features like: " + ", ".join(session["features"]) + ". "

    # === Compile full message history ===
    message_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    if memory_summary:
        message_history.append({"role": "assistant", "content": memory_summary})

    # Append conversation history
    for msg in session["messages"][-10:]:  # keep last 10 turns
        message_history.append(msg)

    # Add latest user message
    message_history.append({"role": "user", "content": request.json.get("message", "")})

    # === Save the new message
    session["messages"].append({"role": "user", "content": request.json.get("message", "")})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=message_history,
            temperature=0.7,
            max_tokens=700
        )
        reply = response.choices[0].message["content"]
        session["messages"].append({"role": "assistant", "content": reply})
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/gallery/<filename>")
def gallery_image(filename):
    return send_from_directory("static/pool_images", filename)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
