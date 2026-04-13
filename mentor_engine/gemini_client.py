"""
Centralized Gemini AI client for WealthPlay.
Supports key failover with multiple API keys for production reliability.
"""

import json 
import os 

import requests 

GEMINI_MODEL =os .environ .get ("GEMINI_MODEL","gemini-2.0-flash")
GEMINI_URL =f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL }:generateContent"


def _gemini_api_keys ():
    """Load Gemini API keys from env with support for multiple key formats."""
    keys =[]


    raw_list =os .environ .get ("GEMINI_API_KEYS","")
    if raw_list :
        keys .extend ([k .strip ()for k in raw_list .split (",")if k .strip ()])


    for env_name in ("GEMINI_API_KEY","GEMINI_API_KEY_1","GEMINI_API_KEY_2"):
        value =os .environ .get (env_name ,"").strip ()
        if value :
            keys .append (value )


    seen =set ()
    ordered_keys =[]
    for key in keys :
        if key not in seen :
            ordered_keys .append (key )
            seen .add (key )

    return ordered_keys 


def gemini_chat (prompt ,system_prompt =None ,temperature =0.7 ,max_tokens =2048 ):
    """
    Send a prompt to Gemini and get a response text.
    Automatically fails over across configured API keys.
    """
    api_keys =_gemini_api_keys ()
    if not api_keys :
        raise Exception ("No Gemini API key configured. Set GEMINI_API_KEYS or GEMINI_API_KEY.")

    contents =[]
    if system_prompt :
        contents .append ({"role":"user","parts":[{"text":system_prompt }]})
        contents .append ({"role":"model","parts":[{"text":"Understood. I will follow these instructions."}]})

    contents .append ({"role":"user","parts":[{"text":prompt }]})

    payload ={
    "contents":contents ,
    "generationConfig":{
    "temperature":temperature ,
    "maxOutputTokens":max_tokens ,
    },
    }

    last_error =None 
    for api_key in api_keys :
        try :
            response =requests .post (
            f"{GEMINI_URL }?key={api_key }",
            json =payload ,
            headers ={"Content-Type":"application/json"},
            timeout =30 ,
            )
            response .raise_for_status ()
            data =response .json ()

            candidates =data .get ("candidates",[])
            if candidates :
                parts =candidates [0 ].get ("content",{}).get ("parts",[])
                if parts :
                    return parts [0 ].get ("text","")

            return "No response generated."
        except requests .exceptions .Timeout as exc :
            last_error =f"timeout: {exc }"
        except requests .exceptions .RequestException as exc :
            last_error =str (exc )

    raise Exception (f"Gemini API failed for all configured keys. Last error: {last_error }")


def gemini_chat_json (prompt ,system_prompt =None ,temperature =0.3 ):
    """Send a prompt to Gemini and parse JSON from the response."""
    text =gemini_chat (prompt ,system_prompt =system_prompt ,temperature =temperature )


    if "```json"in text :
        text =text .split ("```json",1 )[1 ].split ("```",1 )[0 ].strip ()
    elif "```"in text :
        text =text .split ("```",1 )[1 ].split ("```",1 )[0 ].strip ()

    return json .loads (text )
