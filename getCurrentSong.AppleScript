set currentlyPlayingTrack to getCurrentlyPlayingTrack()

-- Method to get the currently playing track
on getCurrentlyPlayingTrack()
  tell application "Spotify"
    set currentArtist to artist of current track as string
    set currentTrack to name of current track as string
  
    return currentArtist & " - " & currentTrack
  end tell
end getCurrentlyPlayingTrack