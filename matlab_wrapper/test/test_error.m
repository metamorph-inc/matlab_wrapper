function test_error(mode)
  if mode == 1
    ME = MException('Component:code', 'Error message');
    throw(ME)
  end
  if mode == 2
    error('Error 2')
  end
  test_error = 42
end
