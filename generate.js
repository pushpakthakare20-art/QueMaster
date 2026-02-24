document.getElementById('generateBtn').addEventListener('click', async () => {
  const subject = document.getElementById('subject').value;
  const topics = Array.from(document.getElementById('topics').selectedOptions).map(opt => opt.value);
  const difficulty = document.getElementById('difficulty').value;
  const marks = document.getElementById('marks').value;
  const title = document.getElementById('title').value;

  if (!subject || topics.length === 0 || !difficulty || !marks) {
    alert("Please fill all required fields.");
    return;
  }

  const payload = {
    subject,
    topics,
    difficulty,
    marks,
    title
  };

  try {
    const res = await fetch('/generate-paper', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    document.getElementById('result').style.display = 'block';
    document.getElementById('result').innerHTML = `
      <h3>✅ Paper Generated!</h3>
      <a href="${data.pdf_url}" target="_blank">Download PDF</a>
    `;
  } catch (err) {
    alert("Something went wrong. Please try again.");
    console.error(err);
  }
});
