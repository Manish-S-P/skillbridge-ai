import Chips from "./Chips";

export default function ProfileCard({ profile }) {
  const name = profile.name || "Candidate";
  return (
    <div className="card profile-card">
      <div className="profile-head">
        <div className="avatar">{name.trim().charAt(0).toUpperCase() || "?"}</div>
        <div>
          <h2>{name}</h2>
          <p className="muted">
            {profile.experience_level || "-"} · Suggested roles: {(profile.suggested_roles || []).join(", ")}
          </p>
        </div>
      </div>
      <p>{profile.summary}</p>
      <h4>Skills found in your resume</h4>
      <Chips items={profile.skills} />
    </div>
  );
}
