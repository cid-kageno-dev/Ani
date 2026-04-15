function buildPrompt(personality, history, currentMessage) {
  const lines = [];

  lines.push("System:");
  lines.push(personality);
  lines.push("");
  lines.push("Conversation:");

  for (const msg of history) {
    if (msg.role === "user") {
      lines.push(`User: ${msg.content}`);
    } else if (msg.role === "assistant") {
      lines.push(`Assistant: ${msg.content}`);
    }
  }

  lines.push(`User: ${currentMessage}`);
  lines.push("Assistant:");

  return lines.join("\n");
}

module.exports = { buildPrompt };
