import argparse,json
def run(task):
 return {'planner':{'model':'gpt-6-sol','instruction':'decompose and state acceptance tests'},'worker':{'model':'gpt-5.4','instruction':'implement only approved changes'},'reviewer':{'model':'gpt-6-sol','instruction':'inspect diff and reject missing tests'},'task':task}
def main():
 p=argparse.ArgumentParser();p.add_argument('task');a=p.parse_args();print(json.dumps(run(a.task),indent=2))
if __name__=='__main__':main()
