_ = """
  @file node_manager.ex
  @author Marcus Edel

  Node handler.
"""

defmodule GymTcpApi.NodeManager do
  def all_nodes do
    Node.list ++ [Node.self]
  end

  def random_node do
    Enum.random(all_nodes)
  end
end
