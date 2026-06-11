def password_page_html(alias: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Password Protected URL</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    background: #060608;
    color: #f1f1f3;
    display: flex; align-items: center; justify-content: center;
    min-height: 100vh; padding: 20px;
  }}
  .container {{
    background: #141417;
    border: 1px solid #23232d;
    border-radius: 16px;
    padding: 40px 32px;
    max-width: 420px; width: 100%;
    text-align: center;
  }}
  .icon {{
    width: 48px; height: 48px;
    margin: 0 auto 20px;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
  }}
  h2 {{ font-size: 22px; font-weight: 700; margin-bottom: 8px; }}
  p {{ color: #a0a0ab; font-size: 14px; margin-bottom: 24px; }}
  input {{
    width: 100%; padding: 14px 16px;
    background: #0f0f14; border: 1.5px solid #23232d;
    border-radius: 12px; color: #f1f1f3; font-size: 15px;
    outline: none; transition: border-color 0.15s; margin-bottom: 12px;
  }}
  input:focus {{ border-color: #3b82f6; }}
  button {{
    width: 100%; padding: 14px 0;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    border: none; border-radius: 12px;
    color: #fff; font-size: 16px; font-weight: 700;
    cursor: pointer; transition: opacity 0.15s;
  }}
  button:disabled {{ opacity: 0.7; cursor: wait; }}
  .error {{
    padding: 12px 16px; margin-top: 12px;
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.25);
    border-radius: 10px; color: #ef4444; font-size: 14px;
    display: none;
  }}
  .error.visible {{ display: block; }}
</style>
</head>
<body>
  <div class="container">
    <div class="icon">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
      </svg>
    </div>
    <h2>Password Protected</h2>
    <p>Enter the password to access: <strong>{alias}</strong></p>
    <form id="pw-form" onsubmit="return handleSubmit(event)">
      <input type="password" id="password" placeholder="Enter password" required autofocus />
      <button type="submit" id="submit-btn">Unlock &amp; Redirect</button>
      <div class="error" id="error">Incorrect password. Try again.</div>
    </form>
  </div>
  <script>
    var alias = '{alias}';
    async function handleSubmit(e) {{
      e.preventDefault();
      var btn = document.getElementById('submit-btn');
      var err = document.getElementById('error');
      btn.disabled = true;
      btn.textContent = 'Verifying...';
      err.classList.remove('visible');
      try {{
        var resp = await fetch('/api/verify/' + alias, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ password: document.getElementById('password').value }}),
        }});
        if (resp.ok) {{
          var data = await resp.json();
          window.location.href = data.long_url;
        }} else {{
          err.classList.add('visible');
          document.getElementById('password').value = '';
          document.getElementById('password').focus();
        }}
      }} catch (_) {{
        err.textContent = 'Something went wrong. Try again.';
        err.classList.add('visible');
      }}
      btn.disabled = false;
      btn.textContent = 'Unlock & Redirect';
      return false;
    }}
  </script>
</body>
</html>"""
