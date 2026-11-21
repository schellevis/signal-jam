const PROFILE_URL_BUILDERS = {
  twitter: (username) => `https://x.com/${username}`,
  tiktok: (username) => `https://www.tiktok.com/@${username}`,
  instagram: (username) => `https://www.instagram.com/${username}/`,
  facebook: (username) => /^\d+$/.test(username)
    ? `https://www.facebook.com/profile.php?id=${username}`
    : `https://www.facebook.com/${username}`,
}

export function parseUsername(platform, input) {
  const trimmed = input.trim()
  const isProfileUrl = trimmed.includes('/')
  if (!isProfileUrl) return trimmed.replace(/^@/, '')

  const url = new URL(trimmed.includes('://') ? trimmed : `https://${trimmed}`)
  const pathSegments = url.pathname.split('/').filter(Boolean)
  if (platform === 'facebook') return parseFacebookUsername(url, pathSegments)
  return (pathSegments[0] ?? '').replace(/^@/, '')
}

function parseFacebookUsername(url, pathSegments) {
  if (pathSegments[0] === 'profile.php') return url.searchParams.get('id') ?? ''
  if (pathSegments[0] === 'people') return pathSegments[2] ?? ''
  return (pathSegments[0] ?? '').replace(/^@/, '')
}

export function buildProfileUrl(platform, username) {
  return PROFILE_URL_BUILDERS[platform](username)
}

export function buildAccountFields(platform, input, displayName) {
  const username = parseUsername(platform, input)
  return {
    platform,
    username,
    account_url: buildProfileUrl(platform, username),
    display_name: displayName.trim() || null,
  }
}
