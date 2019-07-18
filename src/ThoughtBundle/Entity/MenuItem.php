<?php


namespace ThoughtBundle\Entity;

use Doctrine\ORM\Mapping as ORM;
use Gedmo\Mapping\Annotation as Gedmo;

/**
 * Class MenuItem
 * @package ThoughtBundle\Entity
 *
 * @ORM\Entity(repositoryClass="Gedmo\Tree\Entity\Repository\NestedTreeRepository")
 * @ORM\Table(name="menu_items")
 * @Gedmo\Tree(type="nested")
 */
class MenuItem
{

    /**
     * @var int
     *
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    protected $id;

    /**
     * @var string
     *
     * @ORM\Column(type="string", nullable=true)
     */
    public $url;

    /**
     * @var string
     *
     * @ORM\Column(type="string")
     */
    public $text;

    /**
     * @var string
     *
     * @ORM\Column(type="string")
     */
    public $role = 'IS_AUTHENTICATED_ANONYMOUSLY';

    /**
     * @Gedmo\TreeLeft
     * @ORM\Column(name="`left`", type="integer")
     */
    private $left;

    /**
     * @Gedmo\TreeLevel
     * @ORM\Column(name="`level`", type="integer")
     */
    private $level;

    /**
     * @Gedmo\TreeRight
     * @ORM\Column(name="`right`", type="integer")
     */
    private $right;

    /**
     * @Gedmo\TreeRoot
     * @ORM\ManyToOne(targetEntity="ThoughtBundle\Entity\MenuItem")
     * @ORM\JoinColumn(name="tree_root", referencedColumnName="id", onDelete="CASCADE", nullable=true)
     */
    private $root;

    /**
     * @Gedmo\TreeParent
     * @ORM\ManyToOne(targetEntity="ThoughtBundle\Entity\MenuItem", inversedBy="children")
     * @ORM\JoinColumn(name="parent_id", referencedColumnName="id", onDelete="CASCADE", nullable=true)
     */
    private $parent;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\MenuItem", mappedBy="parent")
     * @ORM\OrderBy({"left" = "ASC"})
     */
    private $children;

    /**
     * @var int
     *
     * @ORM\Column(name="`sort`", type="integer", nullable=true)
     */
    private $sort;

    /**
     * @return int
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * @return string
     */
    public function getUrl()
    {
        return $this->url;
    }

    /**
     * @param string $url
     * @return MenuItem
     */
    public function setUrl($url)
    {
        $this->url = $url;
        return $this;
    }

    /**
     * @return string
     */
    public function getText()
    {
        return $this->text;
    }

    /**
     * @param string $text
     * @return MenuItem
     */
    public function setText($text)
    {
        $this->text = $text;
        return $this;
    }

    /**
     * @return mixed
     */
    public function getLeft()
    {
        return $this->left;
    }

    /**
     * @param mixed $left
     * @return MenuItem
     */
    public function setLeft($left)
    {
        $this->left = $left;
        return $this;
    }

    /**
     * @return mixed
     */
    public function getLevel()
    {
        return $this->level;
    }

    /**
     * @param mixed $level
     * @return MenuItem
     */
    public function setLevel($level)
    {
        $this->level = $level;
        return $this;
    }

    /**
     * @return mixed
     */
    public function getRight()
    {
        return $this->right;
    }

    /**
     * @param mixed $right
     * @return MenuItem
     */
    public function setRight($right)
    {
        $this->right = $right;
        return $this;
    }

    /**
     * @return mixed
     */
    public function getRoot()
    {
        return $this->root;
    }

    /**
     * @param mixed $root
     * @return MenuItem
     */
    public function setRoot($root)
    {
        $this->root = $root;
        return $this;
    }

    /**
     * @return mixed
     */
    public function getParent()
    {
        return $this->parent;
    }

    /**
     * @param mixed $parent
     * @return MenuItem
     */
    public function setParent($parent)
    {
        $this->parent = $parent;
        return $this;
    }

    /**
     * @return mixed
     */
    public function getChildren()
    {
        return $this->children;
    }

    /**
     * @param mixed $children
     * @return MenuItem
     */
    public function setChildren($children)
    {
        $this->children = $children;
        return $this;
    }

    public function getRoleString()
    {
        switch ($this->role) {
            case 'IS_AUTHENTICATED_ANONYMOUSLY':
                return 'Unregistered';
            case 'ROLE_USER':
                return 'User';
            case 'ROLE_ADMIN':
                return 'Admin';
            default:
                return 'Undefined';
        }
    }

    /**
     * @return int
     */
    public function getSort()
    {
        return $this->sort;
    }

    /**
     * @param int $sort
     * @return MenuItem
     */
    public function setSort($sort)
    {
        $this->sort = $sort;
        return $this;
    }
}