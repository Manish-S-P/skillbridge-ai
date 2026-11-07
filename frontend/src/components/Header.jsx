export default function Header() {
  return (
    <header className="nav">
      <div className="container nav-inner">
        <a className="brand" href="/">
          <span className="logo">SB</span> SkillBridge <span className="accent">AI</span>
        </a>
        <nav>
          <a href="#how">How it works</a>
          <a href="#upload" className="btn btn-small">Get started</a>
        </nav>
      </div>
    </header>
  );
}
