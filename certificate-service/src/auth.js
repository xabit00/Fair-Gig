const jwt = require("jsonwebtoken");
const { jwtSecret } = require("./config");

function authenticate(req, res, next) {
  const [scheme, token] = (req.headers.authorization || "").split(" ");
  if (scheme !== "Bearer" || !token) {
    return res.status(401).json({ detail: "Authentication required" });
  }
  try {
    const identity = jwt.verify(token, jwtSecret, {
      algorithms: ["HS256"],
      audience: "fairgig-services",
      issuer: "fairgig-auth",
    });
    if (identity.type !== "access") {
      return res.status(401).json({ detail: "Access token required" });
    }
    req.identity = identity;
    return next();
  } catch (error) {
    return res.status(401).json({ detail: "Invalid or expired token" });
  }
}

module.exports = authenticate;

