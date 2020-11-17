<?php

namespace ThoughtBundle\Entity;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\Validator\Constraints as Assert;

/**
 * @ORM\Entity()
 * @ORM\Table(name="teacher_groups")
 */
class TeacherGroup
{
    /**
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    protected $id;

    /**
     * @Assert\NotBlank(message="Emptity")
     * @ORM\Column(name="title", type="string", nullable=true)
     */
    private $title;

    /**
     * @ORM\Column(name="topic_new_lesson", type="text", nullable=true)
     */
    private $topicNewLesson;

    /**
     * @ORM\ManyToMany(
     *     targetEntity="Application\Sonata\UserBundle\Entity\User",
     *     inversedBy="teacherGroup",
     *     cascade={"persist"}
     * )
     * @ORM\JoinTable(name="student_teacher_group")
     */
    private $students;

    /**
     * @ORM\ManyToOne(
     *     targetEntity="Application\Sonata\UserBundle\Entity\User",
     *     inversedBy="studentsGroup"
     * )
     * @ORM\JoinColumn(name="user_id", referencedColumnName="id")
     */
    private $owner;



    public function __construct() {
        $this->students = new ArrayCollection();
    }



    /**
     * @return int|null
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * @return string
     */
    public function getTitle()
    {
        return $this->title;
    }

    /**
     * @return string|null
     */
    public function getTopicNewLesson()
    {
        return $this->topicNewLesson;
    }

    /**
     * @return ArrayCollection
     */
    public function getStudents()
    {
        return $this->students;
    }

    /**
     * @return User
     */
    public function getOwner()
    {
        return $this->owner;
    }

//  Setters

    /**
     * @param string $title
     * @return TeacherGroup
     */
    public function setTitle($title): self
    {
        $this->title = $title;
        return $this;
    }

    /**
     * @param string $topicNewLesson
     * @return TeacherGroup
     */
    public function setTopicNewLesson($topicNewLesson): self
    {
        $this->topicNewLesson = $topicNewLesson;
        return $this;
    }

    /**
     * @param ArrayCollection $students
     * @return TeacherGroup
     */
    public function setStudents(ArrayCollection $students): self
    {
        $this->students = $students;
        return $this;
    }

    /**
     * @param User
     */
    public function setOwner($owner): void
    {
        $this->owner = $owner;
    }



    /**
     * @param User $student
     */
    public function addStudent(User $student) {
        $this->students->add($student);
    }

    /**
     * @param User $student
     */
    public function removeStudent(User $student) {
        $this->students->removeElement($student);
    }

}