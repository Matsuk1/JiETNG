import logging

from flask import Blueprint, jsonify, request

from modules.api_auth import check_user_permission, require_dev_token
from modules.command_config import API_MAX_SEARCH_RESULTS, MAX_SEARCH_RESULTS
from modules.config_loader import read_dxdata
from modules.song_matcher import find_matching_songs


logger = logging.getLogger(__name__)
song_api = Blueprint("song_api", __name__)


def _error(message, status=400):
    return jsonify({"error": "Invalid parameter", "message": message}), status


@song_api.get("/api/v2/songs/search")
@require_dev_token
def search_songs():
    query = request.args.get("q", "")
    try:
        limit = request.args.get("max_results", MAX_SEARCH_RESULTS, type=int)
        if limit < 1:
            return _error("Parameter 'max_results' must be at least 1")
        if limit > API_MAX_SEARCH_RESULTS:
            return _error(f"Parameter 'max_results' must be <= {API_MAX_SEARCH_RESULTS}")

        user_id = request.args.get("user_id")
        requested_version = request.args.get("ver")
        if requested_version:
            version = requested_version.strip().lower()
        elif user_id:
            allowed, user = check_user_permission(user_id, request.token_info["token_id"])
            if not allowed:
                return user
            version = (user or {}).get("version", "jp")
        else:
            version = "jp"

        if version not in ("jp", "intl"):
            return _error("Parameter 'ver' must be 'jp' or 'intl'")
        if query == "__empty__":
            query = ""

        token = request.token_info
        logger.info(
            "[API] Search songs: query=%r, ver=%s, user_id=%s, token_id=%s, note=%s",
            query, version, user_id, token["token_id"], token["note"],
        )
        songs = find_matching_songs(query, read_dxdata(version)[0], max_results=limit)
        if len(songs) > limit:
            return jsonify({
                "error": "Too many results",
                "message": f"Found {len(songs)} songs, please refine your search (max: {limit})",
                "count": len(songs),
            }), 400

        result = [
            {key: song.get(key) for key in ("id", "title", "artist", "type", "version")}
            for song in songs
        ]
        payload = {
            "success": True,
            "count": len(result),
            "query": query,
            "ver": version,
            "songs": result,
        }
        if not result:
            payload["message"] = "No songs found"
        return jsonify(payload)
    except Exception as exc:
        logger.exception("[API] Search songs failed: query=%r", query)
        return jsonify({"error": "Internal server error", "message": str(exc)}), 500


@song_api.get("/api/v1/versions")
@song_api.get("/api/v2/versions")
@require_dev_token
def get_versions():
    try:
        token = request.token_info
        logger.info("[API] Get versions: token_id=%s, note=%s", token["token_id"], token["note"])
        return jsonify({"success": True, "versions": read_dxdata()[1]})
    except Exception as exc:
        logger.exception("[API] Get versions failed")
        return jsonify({"error": "Internal server error", "message": str(exc)}), 500


@song_api.get("/api/v2/dxdata")
@require_dev_token
def get_dxdata():
    version = request.args.get("ver", "jp").strip().lower()
    if version not in ("jp", "intl"):
        return jsonify({"error": "Invalid ver, use jp or intl"}), 400
    songs, versions = read_dxdata(version)
    return jsonify({"songs": songs, "versions": versions})
