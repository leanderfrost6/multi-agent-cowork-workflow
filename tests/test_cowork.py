import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]))
from cowork.run import run
class T(unittest.TestCase):
 def test_roles(self):self.assertEqual([run('x')[x]['model'] for x in ('planner','worker','reviewer')],['gpt-6-sol','gpt-5.4','gpt-6-sol'])
if __name__=='__main__':unittest.main()
