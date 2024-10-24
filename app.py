from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import re
from typing import Optional, Dict, List

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rules.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Define the Node class for AST
class Node:
    def __init__(self, node_type: str, left: Optional['Node'] = None, right: Optional['Node'] = None,
                 value: Optional[str] = None):
        self.node_type = node_type
        self.left = left
        self.right = right
        self.value = value

    def __repr__(self):
        return f"Node(type={self.node_type}, value={self.value}, left={self.left}, right={self.right})"


# Database model for storing rules
class Rule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    rule_string = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Rule(id={self.id}, name={self.name}, rule_string={self.rule_string})"


# Parser function to handle rules
def create_rule(rule_string: str) -> Node:
    rule_string = rule_string.strip()

    if rule_string.startswith('(') and rule_string.endswith(')'):
        rule_string = rule_string[1:-1].strip()

    # Split based on OR and AND
    or_split = re.split(r'\sOR\s', rule_string)
    if len(or_split) > 1:
        left = create_rule(or_split[0].strip())
        right = create_rule(' OR '.join(or_split[1:]).strip())
        return Node("operator", left=left, right=right, value="OR")

    and_split = re.split(r'\sAND\s', rule_string)
    if len(and_split) > 1:
        left = create_rule(and_split[0].strip())
        right = create_rule(' AND '.join(and_split[1:]).strip())
        return Node("operator", left=left, right=right, value="AND")

    return Node("operand", value=rule_string)


# Evaluate function
def evaluate_rule(ast: Node, data: Dict[str, any]) -> bool:
    def evaluate_node(node: Node) -> bool:
        if node.node_type == "operand":
            if ">" in node.value:
                attr, value = re.split(r'>\s*', node.value, maxsplit=1)
                attr = attr.strip()
                value = value.strip()
                try:
                    value = int(value)
                    return data.get(attr) is not None and data.get(attr) > value
                except ValueError:
                    return False
            elif "=" in node.value:
                attr, value = re.split(r'=\s*', node.value, maxsplit=1)
                attr = attr.strip()
                value = value.strip().strip("'")
                return data.get(attr) == value
        elif node.node_type == "operator":
            left_result = evaluate_node(node.left)
            right_result = evaluate_node(node.right)
            if node.value == "AND":
                return left_result and right_result
            elif node.value == "OR":
                return left_result or right_result
        return False

    return evaluate_node(ast)


def combine_rules(rule_strings: List[str]) -> Node:
    combined_node = None
    for rule_string in rule_strings:
        rule_ast = create_rule(rule_string)
        if combined_node is None:
            combined_node = rule_ast
        else:
            combined_node = Node("operator", left=combined_node, right=rule_ast, value="AND")
    return combined_node


# New endpoint to fetch all rule names
@app.route('/get_rule_names', methods=['GET'])
def get_rule_names():
    rules = Rule.query.all()
    rule_names = [rule.name for rule in rules]
    return jsonify(rule_names)


# Route to add a new rule
@app.route('/add_rule', methods=['POST'])
def add_rule():
    data = request.json
    rule_string = data.get('rule')

    if not rule_string:
        return jsonify({'error': 'Rule string is required'}), 400

    rule_name = f"Rule_{len(Rule.query.all()) + 1}"  # Simple naming scheme

    # Create a new rule and add it to the database
    new_rule = Rule(name=rule_name, rule_string=rule_string)
    db.session.add(new_rule)
    db.session.commit()

    # Create an AST node from the rule string
    try:
        ast_node = create_rule(rule_string)
        ast_representation = repr(ast_node)  # Get string representation of the AST node
    except Exception as e:
        return jsonify({'error': f'Error creating AST: {str(e)}'}), 500

    return jsonify({
        'message': 'Rule added successfully',
        'rule': {
            'name': rule_name,
            'rule_string': rule_string,
            'ast': ast_representation
        }
    })


# Modify the evaluate endpoint to accept either rule string or rule name
@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.json
    rule_string = data.get('rule')
    rule_name = data.get('rule_name')
    eval_data = data.get('data')

    if rule_name:
        rule = Rule.query.filter_by(name=rule_name).first()
        if rule:
            rule_string = rule.rule_string
        else:
            return jsonify({'error': 'Rule name not found'}), 404

    if not rule_string or not eval_data:
        return jsonify({'error': 'Rule string/name and data are required'}), 400

    ast = create_rule(rule_string)
    result = evaluate_rule(ast, eval_data)

    return jsonify({'result': result})


# Modify the combine_rules endpoint to accept either rule strings or rule names
@app.route('/combine_rules', methods=['POST'])
def combine_rules_endpoint():
    data = request.json
    rule_strings = data.get('rules')
    rule_names = data.get('rule_names')

    combined_rule_strings = []

    if rule_strings:
        combined_rule_strings.extend(rule_strings)

    if rule_names:
        for name in rule_names:
            rule = Rule.query.filter_by(name=name).first()
            if rule:
                combined_rule_strings.append(rule.rule_string)
            else:
                return jsonify({'error': f'Rule name {name} not found'}), 404

    if not combined_rule_strings:
        return jsonify({'error': 'No valid rules or rule names provided'}), 400

    try:
        combined_ast = combine_rules(combined_rule_strings)
        ast_representation = repr(combined_ast)
    except Exception as e:
        return jsonify({'error': f'Error combining rules: {str(e)}'}), 500

    return jsonify({'combined_rule_ast': ast_representation})


@app.route('/get_rule_string', methods=['GET'])
def get_rule_string():
    rule_name = request.args.get('name')
    rule = Rule.query.filter_by(name=rule_name).first()
    if rule:
        return jsonify({'rule_string': rule.rule_string})
    return jsonify({'error': 'Rule not found'}), 404


# Route to serve index.html
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
    app.run(debug=True)