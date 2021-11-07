import psycopg2
from collections import Counter
from flask_cors import CORS
CORS(app)

# import nltk
# nltk.data.path.append("nltk")
# nltk.download('averaged_perceptron_tagger')
# nltk.download('stopwords')
# nltk.download('wordnet')

from string import ascii_letters
# from nltk.corpus import stopwords
# from nltk.stem import WordNetLemmatizer
# from nltk.tag import pos_tag

from flask import make_response

def tag_trans(S):
    S = S[:2]
    if S == "NN":
        return "n"
    if S == "VB":
        return "v"
    if S == "JJ":
        return "a"
    if S == "RB":
        return "r"
    return "e"

def createWordInsert(wordCountsDict):
    baseQuery = "INSERT INTO queryvec (word, wordount, weight) VALUES "
    startedYet = False
    for k in wordCountsDict:
        if startedYet:
            baseQuery += ","
        baseQuery += "('%s', %i, 0)" % (k, wordCountsDict[k])
        startedYet = True
    baseQuery += ";"
    return baseQuery

def processdoc(data):
    res = ""
    words = []
    for candidate in data.split():
        if all(c in ascii_letters+'-' for c in candidate):
            if len(candidate)==1:
                if candidate[0] in ascii_letters:
                    words.append(candidate)
            else:
                words.append(candidate)
    # print(words)
    # print(words)
    failcount = 0
    wordcount = 0
    for word in words:
        res += (" " + word)
    return res

def parsesend(data):

    conn = None
    try:
        # conn = psycopg2.connect(
            # "sslmode=disable dbname=word-tokens user=postgres hostaddr=/cloudsql/hackrpi2021:us-central1:word-tokens/.s.PGSQL.5432 password=yeNoxLI77EyJahOr")
        conn = psycopg2.connect(host='/cloudsql/hackrpi2021:us-central1:word-tokens/', dbname='word-tokens', user='postgres',  password='yeNoxLI77EyJahOr')
        # create a cursor
        cur = conn.cursor()
        cur.execute('delete from queryvec;')
        cur.execute('update queryscores q\nset score=0;')

        counts = Counter(data.replace("\'","").split())
        insertDataQ = createWordInsert(counts)
        #print(insertDataQ)
        cur.execute(insertDataQ)
        cur.execute("""update queryvec w
set weight=(select (c.idf*log(1+w.wordount)) from collvocab c where c.word = w.word);

update queryscores q
set score=(select (sum(w.weight*v.weight)) from words w, queryvec v where w.docid = q.docid AND w.word = v.word);

WITH length AS (
    SELECT (sqrt(sum(weight*weight))) AS len
    FROM queryvec
)
update queryvec q
set weight=(select (weight/length.len)) from length;

select docid from queryscores where score is not null order by score desc limit 10;""")
        #conn.commit()
        results = cur.fetchall()


        #cur.execute('end;')
        cur.close()
        return results
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')

def main():
    parsesend("black holes")

if __name__ == '__main__':
    main()    




def hello_world(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    print(request)
    print(request.args["query"])
    result = parsesend(request.args["query"])
    print(result)

    headers = {
        'Access-Control-Allow-Origin': '*'
    }
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return ({"message": str(result)}, 204, headers)
    return {"message": str(result)}, 200, headers
    # request_json = request.get_json()
    # if request.args and 'message' in request.args:
    #     return request.args.get('message')
    # elif request_json and 'message' in request_json:
    #     return request_json['message']
    # else:
    #     return f'Hello World!'

