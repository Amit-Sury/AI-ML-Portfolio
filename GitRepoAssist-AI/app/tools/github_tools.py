############## Import packages BEGIN ###########################

#langchain github wrappers
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_core.tools import Tool
from langchain.tools import tool

#pygithub
from github import GithubIntegration, Github

import os
import json
from typing import TypedDict
import matplotlib.pyplot as plt
from pathlib import Path

#my packages
from tools.log_handler import LOG
from tools.github_token_handler import GitTokenHandler
 
######################## END  ###################################


############## Get langchain github tools BEGIN ##################

#get langchain github tools which don't rely on parameters
def get_github_tools():
    
    LOG("Setting up langgraph github tools...")
    try: 
             
        github = GitHubAPIWrapper()
        LOG("Obtaining langgraph GitHubAPIWrapper success")
        toolkit = GitHubToolkit.from_github_api_wrapper(github)
        LOG("Obtaining langgraph toolkit success")

        for github_tool in toolkit.get_tools():
            
            match github_tool.name:
                
                #Below code create tools  without spaces in the name as AWS bedrock
                #expects tool names without spaces
                case "Overview of existing files in Main branch":
                    overview_tool = Tool(
                        name="FileOverview",  # no spaces
                        func=github_tool.run,  # original function
                        description=github_tool.description
                    )
                    LOG("✅ Github Overview tool Initialized.")
                                    
                case "Get Issues":
                    getissues_tool = Tool(
                        name="GetIssues",  # no spaces
                        func=github_tool.run,  # original function
                        description=github_tool.description
                    )
                    LOG("✅ Github Get Issues tool Initialized.")
                    
                    
        return ( overview_tool, getissues_tool)
    except Exception as e:
        LOG(f"❌ Connecting Github failed error: {e}")
        LOG(f"Github Error: {e}")
        return None    
######################## END  ###################################

############## Defining my own github tools BEGIN ################

# issuecomment_tool using github api
@tool
def AddCmtOnIssue(issue_number: int, comment: str):
    """This function adds a comment to issue in github repo. 
    It takes two inputs: 
    
    issue_number: int
    comment: str
    
    Ask user to provide these if these are not available.
    """
    
    LOG(f"Adding comment '{comment}' to issue#{issue_number}")
    try: 
        if not isinstance(issue_number,int) or not isinstance(comment, str):
            return "Invalid input format. Provide issue_number as int and comment as string."
        
        repo = get_repo()
        if not repo:
            return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Could not access GitHub repo"
            })

        #Get the issue with issue_number
        issue = repo.get_issue(number=issue_number)
        LOG(f"Get issue number {issue_number} on repo {os.environ['GITHUB_REPOSITORY']} is successful")
        #create comment on the issue
        issue.create_comment(comment)
        LOG("Creating comment on the issue is successful")

        return f"Operation Successful, adding comment on issue#{issue_number} succeeded!"

    except Exception as e:
        LOG(f"Adding comment on issue#{issue_number} failed") 
        LOG(f"Received exception: {e}")   
        return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Received exception {e} from github"
            })            
        
    
######################## END  ###################################    

# pullreqs_tool using github api
@tool
def GetAllOpenPR():
    """
    Fetches all open pull requests from the repository.

    Args:
        None

    Returns:
        list: A list of dictionaries, each containing PR number and title.
    """
    
    try: 
        repo = get_repo()
        if not repo:
            return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Could not access GitHub repo"
            })

        #Get the issue with issue_number
        pull_reqs = []
        for pr in repo.get_pulls(state="open"):
            pull_reqs.append({"pr_number": pr.number, "pr_title": pr.title})
        
        LOG(f"here are the open PR details: {pull_reqs}")

        return f"Operation Successful, here are the open PR details: {pull_reqs}!"

    except Exception as e:
        LOG(f"Getting open PRs from repo is failed.") 
        LOG(f"Received exception: {e}")   
        return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Received exception {e} from github"
            })                        
        
######################## END  ###################################    

# get details for a specific PR
@tool
def GetPRDetail(pr_number: int):
    """
    Returns details of a specific GitHub pull request (PR).

    Args:
        pr_number (int): The pull request number to fetch details for.

    Returns:
        dict: A dictionary containing PR details such as:
            - pr_number (int): The PR number.
            - title (str): Title of the PR.
            - state (str): State of the PR ('open', 'closed', 'merged').
            - author (str): Username of the PR creator.
            - creation date (str): Creation date of PR
            - base_branch (str): The branch into which the PR is merged.
            - head_branch (str): The branch from which the PR originated.
    """
    
    try: 
        repo = get_repo()
        if not repo:
            return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Could not access GitHub repo"
            })

        #Get details of PR
        pr = repo.get_pull(pr_number)
        pr_detail = []
        pr_detail.append({
            
            "pr_number": pr.number,
            "pr_title": pr.title,
            "pr_state": pr.state,
            "pr_createdby": pr.user.login,
            "pr_created_at": pr.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "pr_baseref": pr.base.ref,
            "pr_headbranch": pr.head.ref,
            "pr_body": pr.body
            
        })
        LOG(f"Getting details for PR#{pr_number} is successful")
        return f"Operation Successful, here are the PR details: {pr_detail}!"

    except Exception as e:
        LOG(f"Getting details of PRs {pr_number} failed.") 
        LOG(f"Received exception: {e}")   
        return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Received exception {e} from github"
            })                        
        
######################## END  ###################################    

# get all the comments for a specific PR
@tool
def ListPRComments(pr_number: int):
    """
    Returns all the comments for a specific GitHub pull request (PR).

    Args:
        pr_number (int): The pull request number to fetch details for.

    Returns:
        dict: A dictionary containing PR details such as:
            - pr_number (int): The PR number.
            - title (str): Title of the PR.
            - total comments (str): Total number of comments on this PR.
        dict: A dictionary containing following details for comments:
            - commented_by (str): Login details of user who gave the comment
            - comment_text (str): detail comment.
    """
    
    try: 
        repo = get_repo()
        if not repo:
            return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Could not access GitHub repo"
            })

        #Get details of PR
        pr = repo.get_pull(pr_number)
        pr_detail = []
        pr_detail.append({
            
            "pr_number": pr.number,
            "pr_title": pr.title,
            "pr_totalcomments": pr.comments
            
        })

        comment_detail = []
        for comment in pr.get_issue_comments():
            comment_detail.append({
                "commented_by": comment.user.login,
                "comment_txt" : comment.body
            })

        LOG(f"Getting comments details for PR#{pr_number} is successful")
        return f"Operation Successful, overview of comments:{pr_detail}, comment details:{comment_detail}"

    except Exception as e:
        LOG(f"Getting details of PRs {pr_number} failed.") 
        LOG(f"Received exception: {e}")   
        return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Received exception {e} from github"
            })                        
        
######################## END  ###################################    

@tool
def GetPRFlsOverview(pr_number: int):
    """
    Returns list of files present in a specific GitHub pull request (PR).

    Args:
        pr_number (int): The pull request number to fetch details for.

    Returns:
        dict: A dictionary containing list of file details such as:
            - file_name (str): Title of the file with path.
            - file_status (str): State of the file ('added', 'modified', 'removed').
            - lines added (str): Number of lines added.
            - lines deleted (str): Number of lines deleted
            - line modified (str): Number of lines modified
            - file difference (str): (Optional) Git diff for that file as a string.
           
    """
    
    try: 
        repo = get_repo()
        if not repo:
            return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Could not access GitHub repo"
            })

        #Get details of PR
        pr = repo.get_pull(pr_number)
        
        pr_files = []

        for f in pr.get_files():
            pr_files.append({
            
            "file_name": f.filename,
            "file_status": f.status,
            "file_total_lines_added": f.additions,
            "file_total_lines_deleted": f.deletions,
            "file_total_lines_modified": f.changes,
            "file_difference" : f.patch
            
        })
        LOG(f"Getting overview of files in PR#{pr_number} is successful")
        return f"Operation Successful, in PR {pr_number} these files are present: {pr_files}!"

    except Exception as e:
        LOG(f"Getting files in PR#{pr_number} failed.") 
        LOG(f"Received exception: {e}")   
        return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Received exception {e} from github"
            })            
    
######################## END  ###################################

#function returns contents of a file in pr
@tool
def PRFlsContent(filename: str, pr_number: int):
    """
    Returns contents of file present in a specific GitHub pull request (PR). 
    Important: you must provide PR number and filename with full path

    Args:
        filename (str): Filename with full path to fetch details for.
        pr_number (int): Pull request (PR) number

    Returns:
        Contents of a file   
    """
    
    try: 
        repo = get_repo()
        if not repo:
            return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Could not access GitHub repo"
            })

        #Get details of PR
        pr = repo.get_pull(pr_number)
        
        content = repo.get_contents(filename, ref=pr.head.ref)
        file_content = content.decoded_content.decode("utf-8")
        LOG(f"Getting contents of file:{filename} in PR#:{pr_number} is successful")

        # language detection from file extension
        ext = Path(filename).suffix.lower()
        ext_to_lang = {
            ".py": "python",
            ".json": "json",
            ".md": "markdown",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".txt": "text",
        }
        language = ext_to_lang.get(ext, "")

        return {
            "language": language,
            "content": file_content,
            "message": "Getting file content is successful.",
        }

        #return json.dumps({
        #    "content": file_content,
        #    "message": f"Getting file content is successful."
        #    })
        #return f"Operation Successful, here are the file contents: {file_content}!"

    except Exception as e:
        LOG(f"Getting file content of file:{filename} failed.") 
        LOG(f"Received exception: {e}")   
        return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Received exception {e} from github"
            })            
######################## END  ###################################


# get list of persons who have open PRs
@tool
def ListPRAuthors():
    """
    Returns list of all the creaters who created a pull request (PR).

    Args:
        None.

    Returns:
        dict: dictionary containing list of PR creaters with details such as:
            - pr.number (str): Number of the PR
            - pr_title (str): Title of the PR.
            - pr_createdby (str): Name of the creator.            
    """
    
    try: 
        repo = get_repo()
        if not repo:
            return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Could not access GitHub repo"
            })

        #Get details of PR
        pr_authors = []
        for pr_list in repo.get_pulls(state="open"):
            LOG(f"Fetching details of PR#{pr_list.number}")
            pr = repo.get_pull(pr_list.number)
            pr_authors.append({
                "pr_number": pr.number,
                "pr_title": pr.title,
                "pr_createdby": pr.user.login
            })
        
        LOG("Getting list of PR authors is successful")
        return f"Operation Successful, here are the list of authors who created PR: {pr_authors}"

    except Exception as e:
        LOG(f"Getting details of PRs failed.") 
        LOG(f"Received exception: {e}")   
        return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Received exception {e} from github"
            })            
######################## END  ###################################    

# get files present in a directory
@tool
def GetFlsfromDirectory(directorypath: str):
    """
    Returns files present in a directory recursively.

    Args:
        directorypath (str): Path of the directory for e.g., "src" or "data/subdir"

    Returns:
        dict: dictionary containing list of all the files in directory recursively:
            - pr.number (str): Number of the PR
            - pr_title (str): Title of the PR.
            - pr_createdby (str): Name of the creator.            
    """
    
    try: 
        repo = get_repo()
        if not repo:
            return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Could not access GitHub repo"
            })

        flsinDirectory = []
        
        lstflsRecursively(repo, directorypath, flsinDirectory)
       
        LOG(f"Getting files in a directory is successful: {flsinDirectory}")
        return f"Operation Successful, here are the list of files in given directory: {flsinDirectory}"

    except Exception as e:
        LOG(f"Getting files in directory failed.") 
        LOG(f"Received exception: {e}")   
        return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Received exception {e} from github"
            })            
    


######################## END  ###################################  

# get content of a file in a directory
@tool
def GetDrctryFlsCnt(flspath: str):
    """
    Returns content of a file in a directory.

    Args:
        flspath (str): Path of the file for e.g., "sample.txt" or "data/subdir/sample.txt"

    Returns:
        Contents of the file            
    """
    
    try: 
        repo = get_repo()
        if not repo:
            return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Could not access GitHub repo"
            })
        
        LOG(f"Getting contents of file: {flspath}...")

        file_content = repo.get_contents(flspath)  # specify branch if needed

        # decode content
        decoded_content = file_content.decoded_content.decode("utf-8")
        LOG(f"Getting files in a directory is successful: {decoded_content[:40]}")

        # language detection from file extension
        ext = Path(flspath).suffix.lower()
        ext_to_lang = {
            ".py": "python",
            ".json": "json",
            ".md": "markdown",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".txt": "text",
        }
        language = ext_to_lang.get(ext, "")

        return {
            "language": language,
            "content": decoded_content,
            "message": "Getting file content is successful.",
        }
        #return json.dumps({
        #    "content": decoded_content,
        #    "message": f"Getting file content is successful."
        #    })
        #return f"Operation Successful, here are the list of files in given directory: {decoded_content}"

    except Exception as e:
        LOG(f"Getting contents of files in directory failed.") 
        LOG(f"Received exception: {e}")   
        return json.dumps({
            "fatal_error": True,
            "message": f"Operation Failed. Received exception {e} from github"
            })            
    
def lstflsRecursively(repo, directorypath, flsinDirectory):
    
    contents = repo.get_contents(directorypath)
    for item in contents:
        if item.type == "file":
            flsinDirectory.append({"File:" : item.path})
        elif item.type == "dir":
            lstflsRecursively(repo, item.path, flsinDirectory)  
 

######################## END  ###################################  

###################### GetRepo BEGIN ############################
def get_repo():
    """This function returns the git repo object"""
    
    try:
        app_id = os.environ["GITHUB_APP_ID"]
        privatekey = os.environ["GITHUB_APP_PRIVATE_KEY"]
        
        LOG("Obtaining access token...")
        access_token = GitTokenHandler(app_id=app_id, private_key=privatekey).get_token()
        LOG("Obtaining access token is successful")

        #Authenticate with your token
        g = Github(access_token)
        LOG("Authentication with your token is successful")

        #Get repo
        repo_name = os.environ["GITHUB_REPOSITORY"]
        LOG(f"Repo name is {repo_name}")
        repo = g.get_repo(repo_name)
        LOG(f"Get repo {repo_name} with access token is successful")
        return repo
    except Exception as e:
        LOG(f"Getting github repo failed: {e}")
        return None

    
############################# END ###############################

######This currently is not getting used in this app############

# Plot graph for authors
class PRAuthors(TypedDict):
    author_name: str
    total_prs: int


@tool
def PltPRAuthors(pr_authors: list[PRAuthors]):
    """
    Generates a plot for authors who have open the PRs.

    Args:
        pr_authors: A list of objects, each with
            - author: name of the PR author (str)
            - total_prs: number of PRs they created (int)
    
    Returns: Message for successful operation
    """

    # Sort pr_authors by total_prs in descending order
    sorted_data = sorted(pr_authors, key=lambda x: x["total_prs"], reverse=True)

    # Extract separate lists if needed for plotting
    authors_sorted = [p["author_name"] for p in sorted_data]
    prs_sorted = [p["total_prs"] for p in sorted_data]


    # Create color palette (each bar a different color)
    colors = plt.cm.tab10(range(len(authors_sorted)))

    # Plot horizontal bar chart
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.barh(authors_sorted, prs_sorted, color=colors)
    ax.set_xlabel("Total PRs")
    ax.set_ylabel("Authors")
    ax.set_title("Pull Requests per Author")
    ax.invert_yaxis()  # Highest PRs at top

    # Add PR count labels at end of each bar
    for bar, value in zip(bars, prs_sorted):
        ax.text(
            value + 0.3,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va='center',
            ha='left',
            fontsize=10,
            fontweight='bold'
        )

    plt.tight_layout()
    #st.pyplot(fig)  # <-- Streamlit-friendly rendering
                    
    return "Operation Successful"    
######################## END  ###################################    