set currentlyPlayingTrack to getCurrentlyPlayingTrack()

-- Method to get the currently playing track
on getCurrentlyPlayingTrack()
  tell application "VLC"
    return get name of current item
  end tell
end getCurrentlyPlayingTrack
